// Azure Advisor Recommendations dimension
// CSV source: AdvisorRecommendations_53329720_YYYYMM.csv
let
    FolderPath = Parameter_ExportFolder,

    Source = Folder.Files(FolderPath),
    // Advisor exports follow pattern: AdvisorRecommendations_53329720_YYYYMM.csv
    FilteredFiles = Table.SelectRows(Source, each
        Text.Contains([Name], "AdvisorRecommendations") and
        Text.EndsWith([Name], ".csv")),

    ProcessFile = (fileContent as binary) =>
    let
        RawCSV = Csv.Document(fileContent, [Delimiter=",", QuoteStyle=QuoteStyle.Csv, Encoding=65001]),
        PromotedHeaders = Table.PromoteHeaders(RawCSV, [PromoteAllScalars=true])
    in
        PromotedHeaders,

    CombinedCSVs = Table.Combine(
        Table.AddColumn(FilteredFiles, "Data", each ProcessFile([Content]))[Data]
    ),

    // Type conversions
    TypedTable = Table.TransformColumnTypes(CombinedCSVs, {
        {"RecommendationId", type text},
        {"Category", type text},
        {"Impact", type text},
        {"ImpactedResource", type text},
        {"PotentialSavings", type number},
        {"Description", type text}
    }),

    // Deduplicate by RecommendationId (keep latest across monthly files)
    Distinct = Table.Distinct(TypedTable, {"RecommendationId"})
in
    Distinct
