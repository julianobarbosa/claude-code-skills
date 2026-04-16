let
    Source = Folder.Files(Parameter_ExportFolder),
    Filtered = Table.SelectRows(Source, each
        Text.Contains([Name], "AdvisorRecommendations") and Text.EndsWith([Name], ".csv")),
    Combined = Table.Combine(
        Table.AddColumn(Filtered, "Data", each
            let
                Raw = Csv.Document([Content], [Delimiter=",", QuoteStyle=QuoteStyle.Csv, Encoding=65001]),
                Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true])
            in
                Headers
        )[Data]
    ),
    // Remove duplicates — keep latest recommendation per RecommendationId
    Deduplicated = Table.Distinct(Combined, {"RecommendationId"}),
    // Explicit type conversions
    Typed = Table.TransformColumnTypes(Deduplicated, {
        {"RecommendationId", type text},
        {"Category", type text},
        {"Impact", type text},
        {"ImpactedResource", type text},
        {"PotentialSavings", type number},
        {"Description", type text}
    }),
    // Null handling — default empty strings and zero savings
    CleanCategory = Table.TransformColumns(Typed, {
        {"Category", each if _ = null or _ = "" then "(sem categoria)" else _, type text}
    }),
    CleanImpact = Table.TransformColumns(CleanCategory, {
        {"Impact", each if _ = null or _ = "" then "(sem impacto)" else _, type text}
    }),
    CleanResource = Table.TransformColumns(CleanImpact, {
        {"ImpactedResource", each if _ = null or _ = "" then "(sem recurso)" else _, type text}
    }),
    CleanSavings = Table.TransformColumns(CleanResource, {
        {"PotentialSavings", each if _ = null then 0 else _, type number}
    }),
    CleanDescription = Table.TransformColumns(CleanSavings, {
        {"Description", each if _ = null or _ = "" then "(sem descricao)" else _, type text}
    })
in
    CleanDescription
