// Power BI Power Query Advanced Editor
let
    Source = Csv.Document(Web.Contents("https://your-hosted-csv-or-local"),[Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.None]),  // Or Excel/File connector
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"Country_Name", type text}, {"Country_Code", type text}, {"Year", Int64.Type}, {"LPI_Score", type number}, {"Customs", type number}, {"Infrastructure", type number}, {"International_Shipments", type number}, {"Logistics_Quality", type number}, {"Tracking_Tracing", type number}, {"Timeliness", type number}}),
    #"Added OnTimeDelivery" = Table.AddColumn(#"Changed Type", "OnTimeDelivery", each if [Timeliness] > 3.5 then "On-Time" else "Delayed", type text),
    #"Added BottleneckFlag" = Table.AddColumn(#"Added OnTimeDelivery", "BottleneckFlag", each if [Infrastructure] < 3.0 then "Bottleneck" else "Normal", type text)
in
    #"Added BottleneckFlag"
