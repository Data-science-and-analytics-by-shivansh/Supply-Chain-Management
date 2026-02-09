-- On-Time Delivery Rate (Assuming Timeliness > 3.5 as 'on-time'; adjust threshold)
SELECT 
    Year,
    AVG(CASE WHEN Timeliness > 3.5 THEN 1 ELSE 0 END) * 100 AS OnTimeDeliveryRate
FROM SupplyChainLPI
GROUP BY Year;

-- Supplier Performance by Country
SELECT 
    Country_Name,
    AVG(LPI_Score) AS AvgSupplierPerformance,
    AVG(Customs) AS AvgCustomsEfficiency
FROM SupplyChainLPI
GROUP BY Country_Name
ORDER BY AvgSupplierPerformance DESC;

-- Inventory Bottlenecks (Low Infrastructure Scores)
SELECT 
    Country_Name,
    Year,
    Infrastructure AS BottleneckScore
FROM SupplyChainLPI
WHERE Infrastructure < 3.0
ORDER BY Infrastructure ASC;

-- Delivery Delays Trends
SELECT 
    Year,
    AVG(Timeliness) AS AvgTimeliness
FROM SupplyChainLPI
GROUP BY Year
ORDER BY Year;

-- What-If Simulation (SQL placeholder; full in Python/Power BI)
SELECT 
    Country_Name,
    LPI_Score,
    LPI_Score * 1.1 AS OptimizedScore  -- Simulate 10% improvement
FROM SupplyChainLPI;
