# Power Query (M) Patterns Reference

Common patterns for .pq files in PBIP semantic models.

## 1. Folder-Based CSV Ingestion

The core pattern for combining multiple billing period CSVs:

```m
let
    Source = Folder.Files(Parameter_ExportFolder),
    Filtered = Table.SelectRows(Source, each
        Text.Contains([Name], "UsageDetails") and Text.EndsWith([Name], ".csv")),
    ProcessFile = (fileContent as binary) =>
    let
        RawCSV = Csv.Document(fileContent, [Delimiter=",", QuoteStyle=QuoteStyle.Csv, Encoding=65001]),
        FirstCell = try RawCSV{0}{0} otherwise "",
        SkipRows = if Text.Contains(FirstCell, "Usage") or Text.Contains(FirstCell, "Report") then 2 else 0,
        Skipped = Table.Skip(RawCSV, SkipRows),
        PromotedHeaders = Table.PromoteHeaders(Skipped, [PromoteAllScalars=true])
    in
        PromotedHeaders,
    Combined = Table.Combine(
        Table.AddColumn(Filtered, "Data", each ProcessFile([Content]))[Data]
    )
in
    Combined
```

Key points:
- `Folder.Files()` discovers all files in the folder
- `Text.Contains` + `Text.EndsWith` filters by naming convention
- Inner function handles per-file processing (header skipping, encoding)
- `Encoding=65001` = UTF-8
- `Table.Combine` merges all processed files

## 2. Column Renaming for Multiple CSV Versions

EA exports change column names across versions. Handle with `List.Accumulate`:

```m
ColumnMapping = {
    {"Date", "UsageDate"},
    {"ExtendedCost", "PretaxCost"},
    {"PreTaxCost", "PretaxCost"},
    {"Cost", "PretaxCost"},
    {"MeterRegion", "ResourceLocation"}
},

RenameExisting = List.Accumulate(
    ColumnMapping,
    PreviousStep,
    (state, pair) =>
        if List.Contains(Table.ColumnNames(state), pair{0}) and pair{0} <> pair{1}
        then Table.RenameColumns(state, {{pair{0}, pair{1}}})
        else state
)
```

Only renames columns that actually exist — safe for mixed-version CSVs.

## 3. Type Conversions

Always explicit, never rely on auto-detection:

```m
TypedTable = Table.TransformColumnTypes(RenameExisting, {
    {"UsageDate", type date},
    {"ConsumedQuantity", type number},
    {"ResourceRate", type number},
    {"PretaxCost", type number}
})
```

### Adding a DateKey Column

```m
AddDateKey = Table.AddColumn(TypedTable, "DateKey", each [UsageDate], type date)
```

## 4. Dimension Derivation from Fact Table

Extract unique dimension values from a fact table:

```m
let
    Source = Fact_Usage,
    Distinct = Table.Distinct(
        Table.SelectColumns(Source, {"SubscriptionGuid", "SubscriptionName", "AccountName", "DepartmentName"})
    )
in
    Distinct
```

For dimensions with classification logic:

```m
let
    Source = Fact_Usage,
    Distinct = Table.Distinct(
        Table.SelectColumns(Source, {"MeterCategory", "MeterSubCategory"})
    ),
    AddTier = Table.AddColumn(Distinct, "ServiceTier", each
        if Text.Contains([MeterCategory], "Virtual Machines") then "Compute"
        else if Text.Contains([MeterCategory], "Storage") then "Storage"
        else if Text.Contains([MeterCategory], "SQL") or Text.Contains([MeterCategory], "Cosmos") then "Database"
        else "Outros",
        type text)
in
    AddTier
```

## 5. JSON Tag Parsing

Parse Azure resource tags from a JSON column:

```m
ParseTag = (tagsJson as nullable text, tagName as text) as nullable text =>
let
    Result = if tagsJson = null or tagsJson = "" then null
             else try Json.Document(tagsJson){[Key=tagName]}[Value]
                  otherwise
                      try Record.Field(Json.Document(tagsJson), tagName)
                      otherwise null
in
    Result,

AddExecutivo = Table.AddColumn(Source, "Executivo", each
    let tag = ParseTag([Tags], "Executivo")
    in if tag = null then "(nao atribuido)" else tag, type text),

AddTagCompliance = Table.AddColumn(Previous, "TagsCompletas", each
    [TemTagExecutivo] and [TemTagGestor] and [TemTagRotulo] and [TemTagAgrupamento] and [TemTagAmbiente],
    type logical)
```

The `ParseTag` function handles two JSON formats:
- Array of objects: `[{"Key":"Executivo","Value":"Allan Lima"}]`
- Simple record: `{"Executivo":"Allan Lima"}`

## 6. Calendar Table Generation (pt-BR)

```m
let
    StartDate = #date(2024, 1, 1),
    EndDate = #date(2027, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    Typed = Table.TransformColumnTypes(DateTable, {{"Date", type date}}),

    AddAno = Table.AddColumn(Typed, "Ano", each Date.Year([Date]), Int64.Type),
    AddMes = Table.AddColumn(AddAno, "Mes", each Date.Month([Date]), Int64.Type),

    MonthNames = {"Janeiro","Fevereiro","Marco","Abril","Maio","Junho",
                  "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"},
    AddNomeMes = Table.AddColumn(AddMes, "NomeMes", each MonthNames{[Mes]-1}, type text),

    MonthAbbrev = {"Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"},
    AddAbrev = Table.AddColumn(AddNomeMes, "NomeMesAbrev", each MonthAbbrev{[Mes]-1}, type text),

    AddAnoMes = Table.AddColumn(AddAbrev, "AnoMes", each
        Text.From([Ano]) & Text.PadStart(Text.From([Mes]), 2, "0"), type text),
    AddLabel = Table.AddColumn(AddAnoMes, "AnoMesLabel", each
        [NomeMesAbrev] & "/" & Text.From([Ano]), type text),

    AddTrimestre = Table.AddColumn(AddLabel, "Trimestre", each
        "T" & Text.From(Number.RoundUp([Mes] / 3)), type text),

    DayNames = {"Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"},
    AddDiaSemana = Table.AddColumn(AddTrimestre, "DiaSemana", each
        DayNames{Date.DayOfWeek([Date], Day.Monday)}, type text),

    AddEhDiaUtil = Table.AddColumn(AddDiaSemana, "EhDiaUtil", each
        Date.DayOfWeek([Date], Day.Monday) < 5, type logical)
in
    AddEhDiaUtil
```

## 7. Key-Value CSV Parsing (EA Balance)

EA Balance exports use a key-value format, not tabular:

```m
let
    Source = Folder.Files(Parameter_ExportFolder),
    Filtered = Table.SelectRows(Source, each
        Text.Contains([Name], "ArmBalances") and Text.EndsWith([Name], ".csv")),

    ProcessBalance = (content as binary, fileName as text) =>
    let
        Lines = Lines.FromBinary(content, null, null, 65001),
        // Extract billing period from filename: ArmBalances_53329720_YYYYMM_en.csv
        Period = Text.BetweenDelimiters(fileName, "_", "_", 1),
        // Parse key-value lines: "Key,Currency,Value"
        ParseLine = (line as text) =>
            let parts = Text.Split(line, ",")
            in if List.Count(parts) >= 3 then {parts{0}, parts{2}} else null,
        Parsed = List.Select(List.Transform(Lines, ParseLine), each _ <> null),
        AsRecord = Record.FromList(
            List.Transform(Parsed, each _{1}),
            List.Transform(Parsed, each _{0})
        )
    in
        Record.AddField(AsRecord, "BillingPeriod", Period)
in
    ...
```

## 8. Parameter Usage

Create a configurable parameter in a .pq file:

```m
"C:\data\billing-exports" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
```

Reference in other queries:

```m
let
    FolderPath = Parameter_ExportFolder,
    Source = Folder.Files(FolderPath),
    ...
```

## 9. Null Handling Patterns

```m
// Replace null ResourceGroup
CleanRG = Table.TransformColumns(Previous, {
    {"ResourceGroup", each if _ = null or _ = "" then "(sem grupo)" else _, type text}
}),

// Default for missing tags
AddTag = Table.AddColumn(Previous, "Executivo", each
    let tag = ParseTag([Tags], "Executivo")
    in if tag = null then "(nao atribuido)" else tag, type text),

// Safe number conversion (null → 0)
SafeNumber = Table.TransformColumns(Previous, {
    {"PretaxCost", each if _ = null then 0 else _, type number}
})
```

## Tips

- Always specify `Encoding=65001` (UTF-8) for CSV parsing
- Use `try ... otherwise` for resilient parsing
- Filter files early (`Table.SelectRows` on file names) before processing content
- Test each step individually in Power Query Editor before combining
- Use `Table.Buffer()` for tables referenced multiple times (performance)
