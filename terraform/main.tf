# TEMPLATE ONLY - NOT plan/apply validated against a live tenancy.
# Built-in resource: OCI Container Instances container instance.
# Field names per the oracle/oci provider docs (oci_container_instances_container_instance).
# Conventions shown: pinned image tag, explicit restart policy, explicit graceful
# shutdown timeout, no secrets in environment_variables (use OCI Vault instead).

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

variable "compartment_id" {
  type        = string
  description = "OCID of the compartment"
}

variable "availability_domain" {
  type        = string
  description = "Availability domain name"
}

variable "subnet_id" {
  type        = string
  description = "OCID of the subnet for the instance VNIC"
}

resource "oci_container_instances_container_instance" "api" {
  compartment_id             = var.compartment_id
  availability_domain        = var.availability_domain
  display_name               = "webshop-api"
  shape                      = "CI.Standard.E4.Flex"
  container_restart_policy   = "ALWAYS" # right for a server; use ON_FAILURE for jobs
  graceful_shutdown_timeout_in_seconds = 30

  shape_config {
    ocpus         = 1
    memory_in_gbs = 4
  }

  vnics {
    subnet_id             = var.subnet_id
    is_public_ip_assigned = false
  }

  containers {
    display_name = "api"
    image_url    = "iad.ocir.io/tenancy/webshop/api:v1.4.3" # pinned tag, never bare/latest

    environment_variables = {
      LOG_LEVEL = "info" # no secrets here - inject them from OCI Vault at runtime
    }
  }
}
