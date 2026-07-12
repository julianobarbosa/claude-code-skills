# Diagnosis: Power BI Cost Management Connector — Access Denied

## Root Cause

The Power BI Cost Management connector for EA enrollments does NOT use Azure RBAC roles. When Rogerio enters enrollment number 53329720, the connector authenticates against the EA Billing API, which has its own separate permission system managed through the EA Portal (ea.azure.com). His "Cost Management Reader" role on the subscription is completely irrelevant to this authentication path.

## Fix

Rogerio needs an **Enterprise Administrator (Read-Only)** role assigned at the EA enrollment level in the EA Portal. An existing Enterprise Admin must grant this. After assignment, wait ~30 minutes for propagation, then retry.
