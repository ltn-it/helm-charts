# openshift-ingressOperatorPatch

Set `nodePlacement` to the native OpenShift `IngressController.spec.nodePlacement`
object to configure router node selection and tolerations. The default `{}` omits
the field and preserves the operator's placement defaults.

For example, select infrastructure nodes and tolerate their scheduling taint:

```yaml
nodePlacement:
  nodeSelector:
    matchLabels:
      node-role.kubernetes.io/infra: ""
  tolerations:
    - key: infra
      operator: Equal
      value: reserved
      effect: NoSchedule
```

Use the key, value and effect actually configured on the target nodes. Changing
placement can roll the router deployment; verify spare capacity and router
availability before applying it. Certificate and wildcard settings remain
independent of placement. This setting configures routers, not ingress canaries
or other platform components.
