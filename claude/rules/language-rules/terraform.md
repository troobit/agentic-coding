---
paths:
  - "**/*.tf"
  - "**/*.tfvars"
  - "**/*.tofu"
  - "**/*.hcl"
---

# Terraform & OpenTofu Style Guide

A personal reference for writing Terraform/OpenTofu. Distilled from three working codebases:

- **The OpenTofu stacks** — Azure stacks (`az_vnet`, `az_container_webapp`, `az_pep_service`, `az_private_endpoints`, `az_monitoring`) and AWS stacks (`aws/vpc`, `aws/simple_ec2`)
- **The Entra/tenant tree** — a Terraform root module composing `./modules/*` for management groups, identity, app registrations, conditional access
- **The identity stack** — data-driven Entra users, groups, and role assignments built from typed map variables

Where the three agree, the convention is strong. Where they disagree, both options are listed with the trade-off. The same working practice as the other repos applies: specs live in `specs/`, tasks in a rune task file, decisions in `decision_log.md`.

---

## 1. Baseline

- **OpenTofu (`tofu`) is the default binary for new work.** The language is the same HCL; existing Terraform stacks stay on `terraform` until migrated deliberately.
- `required_version` is a floor, not a pin: `>= 1.7.5`. Provider versions are pinned with `~>` in `required_providers` (`~> 3.109.0`).
- **`tofu fmt -recursive` before every commit.** Attribute alignment inside a block is `fmt`'s job — never hand-align to a different rule.
- `tofu validate` → `tofu plan` → review → `tofu apply`. Run tflint where it is configured. If the repo has a Makefile, use its targets.
- The marker tag on generated resources is `OpenTofu = "true"` for new stacks; `Terraform = "true"` is the legacy spelling and is only kept where changing it would churn state.

---

## 2. Repository Layout

One directory per root module — a *stack*. Stacks are self-contained and never read each other's resources.

```
tofu/
├── az_container_webapp/           # a stack: one root module, one state file
│   ├── backend.tf                 # empty backend block, config supplied at init
│   ├── providers.tf               # provider config for this stack
│   ├── variables.tf               # stack-wide inputs
│   ├── outputs.tf                 # what pipelines and humans need back
│   ├── main.tf                    # the spine: data sources, RG, top-level composition
│   ├── keyvault.tf                # one file per concern
│   ├── containerapp.tf
│   ├── environments/
│   │   └── dev-backend.hcl.example
│   ├── example.tfvars
│   └── modules/                   # local modules, owned by this stack
│       ├── umid/                  # main.tf, variables.tf, outputs.tf, versions.tf
│       └── vnet/
└── aws/vpc/
    ├── config/networks.yml        # data-driven topology
    ├── providers.tf               # aliased providers per account
    ├── vpc.tf
    └── routetable.tf
```

- **Stack directories are named `<provider>_<purpose>`** (`az_pep_service`, `az_private_endpoints`). The directory name is the stack name and matches the state key (`key = "az_private_endpoints.tfstate"`).
- **Files split by concern, not by resource type.** `network.tf` holds the vnet, its subnets and its NICs; `keyvault.tf` holds the vault, its role assignments and its secrets. Never a `resources.tf`.
- **`main.tf` is the spine**: data sources, the resource group, and the top-level module calls. If `main.tf` grows past that, the new material wanted its own file.
- **Cross-stack values travel as inputs**, not as remote state reads. The private link service alias produced by one stack is passed into the consuming stack through tfvars, with a comment naming the producer.
- **Disabled files get a `.tf.ignore` suffix** (`jumphost.tf.ignore`). The file stays readable and out of the graph — better than commenting out its entire contents.

---

## 3. Comment Banners

The signature of this codebase. Every logical section opens with a three-line banner.

```hcl
# =============================================================================
# Key Vault
# =============================================================================

resource "azurerm_key_vault" "this" {
  ...
}
```

Rules:

- The rule line is `#`, one space, then 77 `=` — **79 columns total**. `fmt` does not reflow comments, so the width is yours to keep. Make it an editor snippet.
- **Title Case, short noun phrase**, naming what the section builds: `Data Sources`, `Resource Groups`, `Virtual Network - Subnets`, `Container App UMID (for Keyvault access)`. Not a sentence, not a verb phrase — except the file-opening banner, which may carry one full sentence explaining what the whole file does:

  ```hcl
  # =============================================================================
  # This section goes through creating the vnet and nics for the private link services.
  # =============================================================================
  ```

- Blank line before the opening rule, blank line after the closing rule.
- **Short files still get banners.** A twelve-line `main.tf` carries `# Variables` and `# Create RG`. The banner is the table of contents, not a size-triggered decoration.
- **Don't nest banners.** A section needing sub-structure gets plain `#` comment lines, or the file gets split.
- The lighter `### VPC` three-hash form in the older AWS trees is legacy. New code uses the full banner.

### Inline and explanatory comments

- Trailing `#` comments carry the *reason*, not the restatement:

  ```hcl
  sku = "PerGB2018" # "Free" sku was retired by Azure and rejected by current azurerm providers
  ```

- Comments above a `local` or a `for` expression explain the shape being built, not the syntax:

  ```hcl
  # flatten ensures that this local value is a flat list of objects, rather
  # than a list of lists of objects.
  ```

- **Commented-out code needs a reason line or it gets deleted.** Retaining an alternative is legitimate when the comment says why:

  ```hcl
  # Removing KV Access admin for TF agent - as it is inherited from subscription level
  # resource "azurerm_role_assignment" "kv_data_access_administrator" { ... }
  ```

- `#`, never `//`.

---

## 4. Where Variables Live

The codebases disagree, and both readings are defensible:

| Option | Where it is used | Trade-off |
|---|---|---|
| Central `variables.tf` | Module trees, the identity stack | One place to read the interface; the declaration is far from its use |
| Declared in the file that uses them, under a `# Variables` banner | `az_pep_service`, `az_private_endpoints` | The name, its default and its resource are on one screen; the stack's interface is scattered |

**Rule:** stack-wide inputs (`subscription_id`, `tenant_id`, `location`, `common_tags`, anything a tfvars file sets) go in `variables.tf`. A variable used by exactly one file, whose default is really a constant (`endpointsvc_vnet_name = "endpointsvc-vnet"`), may sit under a `# Variables` banner at the top of that file. **Modules always use `variables.tf`** — no exceptions, because the module's interface is its contract.

---

## 5. Variables

- **Always declare `type`.** An untyped variable is a bug waiting for a tfvars typo.
- **`description` on every module variable**, and on any stack variable whose name doesn't fully explain it. Say what the value is *for*, and what to pass: *"subnetID in which the resource will be deployed. Pass azure_rm.subnet.id to this module"*.
- **Typed object maps for data-driven inputs**, with `optional()` for the parts that have sensible defaults:

  ```hcl
  variable "users" {
    type = map(object({
      display_name  = string
      mail_nickname = string
      # keys into var.groups this user should be a member of
      groups = optional(list(string), [])
      role_assignments = optional(list(object({
        role_definition_name = string
        scope                = string
      })), [])
    }))
    description = "Users to create, keyed by a stable short name"
    default     = {}
  }
  ```

- **`validation` for anything checkable**:

  ```hcl
  validation {
    condition     = can(regex("^(\\d{1,3}\\.){3}\\d{1,3}/\\d{1,2}$", var.vnet_cidr))
    error_message = "CIDR block must be in the format of x.x.x.x/x"
  }
  ```

- `map(any)` is acceptable for tags. Nothing else.
- **No secrets in defaults.** Secret values arrive through a gitignored `*.auto.tfvars` or a key vault reference.
- **Commit the templates**: `example.tfvars` and `environments/<env>-backend.hcl.example`, each with a header comment giving the copy-to instruction:

  ```hcl
  # copy to <name>.auto.tfvars (auto-loaded, gitignored) and fill in real values
  ```

---

## 6. Naming

- **HCL labels are snake_case.** `azurerm_key_vault_secret "cr-password"` is legacy; new code writes `cr_password`.
- **`this` is the label for a stack's or module's singleton** of a type: `azurerm_resource_group.this`, `azurerm_virtual_network.this`. When several of the same type coexist, label by role: `endpointsvc_vnet`, `ingress_rg`, `privatelinks`.
- **Rendered cloud names carry a type prefix**, built by interpolation at the point of use or in a `local` — never baked into a variable default:

  ```hcl
  name = "nsg-${each.key}"        # or "mi-${var.name}", "sn-${each.key}", "pvtendpoint-${var.plinkname}"
  ```

- Counted names zero-pad so they sort: `"endpoint-vm-nic-${format("%02d", count.index + 1)}"`.

---

## 7. Modules

**Write a local module when** the same cluster of resources appears more than once, or when one resource always needs a fixed set of companions — an identity plus its role assignments, a vnet plus its subnets plus their NSGs and associations.

**Don't wrap a single resource** unless the wrapper adds something real: naming, defaults, or the companion resources above.

- **Module files**: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`.
- **`versions.tf` declares `required_providers` only — never a `provider` block.** Providers are configured by the root module and inherited. A module that configures its own provider cannot be `for_each`'d and cannot be reused across accounts.
- **The module interface is flat**: scalars plus one typed map or list for the repeated thing. The *caller* does the `for_each`:

  ```hcl
  module "vnet" {
    for_each            = var.vnet_config
    source              = "./modules/vnet"
    vnet_name           = each.key
    vnet_cidr           = each.value.vnet_cidr
    location            = azurerm_resource_group.this.location
    resource_group_name = azurerm_resource_group.this.name
    subnets             = each.value.subnets
    tags                = var.common_tags
  }
  ```

- **Argument order at the call site**: `for_each`/`count` first, then `source`, then identity arguments, then configuration, then `depends_on` last.
- **Registry modules are pinned to an exact version** (`version = "3.18.1"`), never floating, and get their own banner at the call site.
- **Module outputs are the ids callers need**, one output per value (`id`, `principal_id`, `client_id`), `sensitive = true` where warranted.
- Local modules live under the stack that owns them. A module used by two stacks moves up to a shared `modules/` directory and gains a version pin.

---

## 8. Iteration

- **`for_each` by default. `count` only as an on/off switch:**

  ```hcl
  # For creating based on whether "value" is true or false - good trick for modules with different options.
  count = var.type == "value" ? 1 : 0
  ```

- **Convert lists to maps at the point of use**, keyed on something stable:

  ```hcl
  # for_each block needs a map, so the for element creates a map with the name as the keys
  for_each = { for k, v in local.vnets : v.name => v }

  # composite key where the name alone isn't unique
  for_each = { for k, v in local.subnets : "${v.vnet}-${v.name}" => v }
  ```

- **Keys must be stable.** A changed key destroys and recreates. Key on names, never on list position.
- **`dynamic` blocks for optional nested blocks** (subnet delegations, IP configurations), driven by the same map.

---

## 9. Data-Driven Stacks

Topology that a reviewer should read as data lives in YAML next to the stack, decoded into locals:

```hcl
# =============================================================================
# Data feed from YAML file
# =============================================================================
locals {
  vnet_data = yamldecode(file("./config/networks.yml"))

  # flatten ensures that this local value is a flat list of objects, rather
  # than a list of lists of objects.
  vnets = flatten([
    for vnet_key, vnet in local.vnet_data : [
      {
        name     = vnet.name
        location = vnet.location
        cidr     = vnet.cidr
      }
    ]
  ])
}
```

- Adding a subnet is then a data change, reviewed as a YAML diff.
- The decoded locals are flattened into lists, then turned into maps by `for_each` at the resource.
- **The YAML belongs to one stack.** If two stacks need the same data it becomes a variable or a module input, not a shared file read by relative path.
- The equivalent for smaller data sets is a typed `map(object({...}))` variable filled from tfvars — same shape, no file read. Prefer the variable when the data is short enough to sit in tfvars.

---

## 10. Tags

- Every taggable resource takes tags. The stack carries a `common_tags` variable and merges per-resource facts in:

  ```hcl
  tags = merge(var.common_tags, { "ResourceType" = "Resource Group" }, { "ResourceName" = var.rg_name })
  ```

- **Tag keys are consistent within a stack.** The `"ResourceType"` / `"Resource Type"` pair that exists in the older Azure code is a defect, not a variant.
- **AWS uses provider `default_tags`** instead of per-resource merging:

  ```hcl
  provider "aws" {
    profile = var.aws_profile
    alias   = "dev"
    default_tags {
      tags = { OpenTofu = "true" }
    }
  }
  ```

---

## 11. Dependencies

**Reference the attribute; don't pass the name and add `depends_on`.**

```hcl
# preferred - the graph sees the edge
resource_group_name = azurerm_resource_group.this.name

# avoid - a string plus a manual edge
resource_group_name = var.rg_name
depends_on          = [azurerm_resource_group.this]
```

Explicit `depends_on` is for dependencies that are real but invisible to the graph:

- a role assignment that must land before a secret write (`azurerm_key_vault_secret` depending on `azurerm_role_assignment.kv_administrator`)
- RBAC or DNS propagation that the provider doesn't model
- a module whose side effects must settle before the next module starts

This is where the older Azure stacks drift most — they pass `var.rg_name` and then bolt on `depends_on`. New and touched code uses the reference.

---

## 12. State, Backends, and Secrets

- **The backend block is empty; configuration arrives at init:**

  ```hcl
  terraform {
    # backend values are environment-specific and supplied at init time:
    #   tofu init -backend-config=environments/dev-backend.hcl
    backend "azurerm" {}
  }
  ```

- Commit `*.hcl.example` and `example.tfvars`; keep the real files local. The stack's `.gitignore`:

  ```gitignore
  # local provider caches and state
  .terraform/
  *.tfstate
  *.tfstate.*
  crash.log
  crash.*.log

  # real per-environment config stays local; committed *.example files are the templates
  *-backend.hcl
  *.tfvars
  !example.tfvars
  ```

- **Commit `.terraform.lock.hcl`.** The existing stacks ignore it, which means two machines can silently plan against different provider builds. Ignore it only for throwaway POC stacks, and say so in the file.
- State never enters the repository. Secrets never enter a committed tfvars.

---

## 13. Providers and Authentication

- One `providers.tf` per stack, opening with its banner. Subscription and tenant come from variables — never a literal GUID without a comment naming what it is:

  ```hcl
  role_id = "62e90394-69f5-4237-9190-012177145e10" # Global Administrator role ID
  ```

- **Pipelines authenticate with OIDC** (`use_oidc = true`) against a user-assigned managed identity. No client secrets in files.
- **AWS multi-account: one aliased provider per account**, each with `assume_role` and a `default_tags` block. Pass `providers = { aws = aws.dev }` explicitly at module call sites rather than relying on inheritance.

---

## 14. Outputs

- `outputs.tf` at the stack root exposes what pipelines and operators need back: ids, URIs, names.
- Names are snake_case and describe the value: `kv_uri`, `container_app_env_id`, `umid_id`.
- `sensitive = true` on anything secret-bearing. `description` on module outputs; stack outputs may go without when the name says it.
- Outputs are an interface — removing one is a breaking change for whatever consumes the stack.

---

## 15. Lifecycle

Use `ignore_changes` where another system owns the value, and say who:

```hcl
lifecycle {
  ignore_changes = [
    tags["file-encoding"], # written by the pipeline that uploads the secret
    value                  # rotated outside Terraform
  ]
}
```

Prefer keeping fragile resources out of a stack that gets destroyed over reaching for `prevent_destroy`.

---

## 16. Known Rough Edges

Present in the checked-in code, not the standard. When touching these files, fix them:

- **`depends_on` where a reference would do** — see §11.
- **`.terraform.lock.hcl` gitignored** — see §12.
- **Hyphenated HCL labels** (`cr-password`) and unprefixed variable names in older modules (`rgname`, `subnetid`, `plinkname`) — new modules use snake_case throughout.
- **Mixed tag keys** within one stack (`ResourceType` vs `Resource Type`).
- **Hardcoded literals in module bodies** — a repository name inside the UMID module's tags belongs in a variable.

---

## 17. Working Practice

Same as the other repos:

- A change with any design content gets a `specs/<feature>/` folder — requirements, design, a rune task file, `decision_log.md` in Enhanced Nygard format.
- How a stack is actually initialised and deployed (backend config, pipeline identity, manual steps) goes in `docs/agent-notes/`, not in tribal memory.
- `tofu fmt` and `tofu validate` before commit; a reviewed `plan` before every apply.
