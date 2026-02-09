// Excel Power Query: Data > Get Data > Blank Query
let
    Source = Csv.Document(File.Contents("C:\path\to\data\lpi_dataset.csv"),[Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"Country_Name", type text}, {"Country_Code", type text}, {"Year", Int64.Type}, {"LPI_Score", type number}, {"Customs", type number}, {"Infrastructure", type number}, {"International_Shipments", type number}, {"Logistics_Quality", type number}, {"Tracking_Tracing", type number}, {"Timeliness", type number}}),
    #"Added OnTimeRate" = Table.AddColumn(#"Changed Type", "OnTimeRate", each if [Timeliness] > 3.5 then 1 else 0, Int64.Type),
    #"Grouped by Year" = Table.Group(#"Added OnTimeRate", {"Year"}, {{"AvgOnTimeRate", each List.Average([OnTimeRate]) * 100, type number}})
in
    #"Grouped by Year"
