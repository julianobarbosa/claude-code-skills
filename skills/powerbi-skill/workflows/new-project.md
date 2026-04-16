# Workflow: New PBIP Project

Scaffold a new Power BI Project (PBIP) from scratch with git-friendly structure.

## Steps

### 1. Create Directory Structure

```
ProjectName/
├── ProjectName.pbip
├── ProjectName.Report/
│   ├── report.json
│   ├── definition.pbir
│   └── StaticResources/SharedResources/BaseThemes/
├── ProjectName.SemanticModel/
│   ├── definition.pbism
│   └── definition/
│       ├── model.tmdl
│       ├── tables/
│       ├── expressions/
│       └── relationships.tmdl
├── scripts/
└── docs/
```

### 2. Create .pbip File

```json
{
  "version": "1.0",
  "artifacts": [
    {
      "report": {
        "path": "ProjectName.Report"
      }
    },
    {
      "dataset": {
        "path": "ProjectName.SemanticModel"
      }
    }
  ]
}
```

### 3. Create definition.pbism

```json
{
  "version": "1.0",
  "settings": {}
}
```

### 4. Create definition.pbir

```json
{
  "version": "1.0",
  "datasetReference": {
    "byPath": {
      "path": "../ProjectName.SemanticModel"
    }
  }
}
```

### 5. Create model.tmdl

```
model Model
    culture: pt-BR
    defaultPowerBIDataSourceVersion: powerBI_V3
    sourceQueryCulture: pt-BR
```

Adjust `culture` to match the project locale.

### 6. Create _Measures Table

In `tables/_Measures.tmdl`:

```
table _Measures
    lineageTag: measures-001

    column MeasureColumn
        dataType: int64
        isHidden: true
        lineageTag: measures-col
        summarizeBy: none
        sourceColumn: none

    partition _Measures = calculated
        source = ROW("MeasureColumn", 0)
```

### 7. Create Parameter Expression

In `expressions/Parameter_ExportFolder.pq` (if using folder-based ingestion):

```m
"C:\data\exports" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
```

### 8. Create relationships.tmdl

Start with a comment header:

```
// Star Schema Relationships - All Many-to-One from Facts to Dimensions
```

Add relationships as tables are created.

### 9. Create Theme (Optional)

In `StaticResources/SharedResources/BaseThemes/CustomTheme.json`:

```json
{
  "name": "CustomTheme",
  "dataColors": ["#003366", "#0066CC", "#FF6600", "#339966", "#CC3333", "#9933CC"],
  "background": "#FFFFFF",
  "foreground": "#333333",
  "tableAccent": "#0066CC"
}
```

### 10. Initialize Git

```bash
git init
# Add .gitignore for PBI artifacts
echo "*.pbit" >> .gitignore
echo ".pbi/" >> .gitignore
echo "*.pbix" >> .gitignore
```

## Checklist

- [ ] .pbip opens in Power BI Desktop
- [ ] model.tmdl has correct culture setting
- [ ] _Measures table exists with hidden column
- [ ] Parameter configured for data source
- [ ] relationships.tmdl created (even if empty)
- [ ] Git initialized with .gitignore
