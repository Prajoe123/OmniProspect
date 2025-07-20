import type { Express, Request, Response } from "express";
import { complianceMiddleware } from "../middleware/compliance";

export function registerComplianceRoutes(app: Express) {
  // Get compliance guidelines (must be before platform-specific routes)
  app.get("/api/compliance/guidelines", (_req: Request, res: Response) => {
    const guidelines = {
      linkedin: {
        dailyLimit: 100,
        accountType: "free",
        delays: "2-3 seconds between requests",
        dataTypes: ["public profiles", "company information", "public posts"],
        prohibited: ["private messages", "personal data", "excessive automation"],
        terms: "https://www.linkedin.com/legal/user-agreement"
      },
      google: {
        dailyLimit: 100,
        apiType: "Custom Search API",
        cost: "$5 per 1,000 queries after free tier",
        dataTypes: ["web search results", "company websites", "public information"],
        prohibited: ["direct search result scraping", "automated queries without API"],
        terms: "https://developers.google.com/terms"
      },
      bing: {
        monthlyLimit: 1000,
        apiType: "Web Search API",
        cost: "Various Azure pricing tiers",
        dataTypes: ["web search results", "business information", "public content"],
        prohibited: ["unauthorized API usage", "exceeding subscription limits"],
        terms: "https://azure.microsoft.com/en-us/support/legal/"
      },
      yahoo: {
        rateLimit: "1-2 requests per second",
        method: "Web scraping with robots.txt compliance",
        cost: "Free (rate limited)",
        dataTypes: ["search results", "public web content"],
        prohibited: ["ignoring robots.txt", "excessive request rates", "private content"],
        terms: "Standard web scraping best practices"
      }
    };

    res.json({
      guidelines,
      lastUpdated: "2025-01-14",
      version: "1.0",
      generalPrinciples: [
        "Only collect publicly available information",
        "Respect platform terms of service and rate limits",
        "Use data for legitimate business purposes only",
        "Provide clear opt-out mechanisms for contacts",
        "Maintain proper security and privacy controls"
      ]
    });
  });

  // Get compliance status for all platforms
  app.get("/api/compliance/status", (req: Request, res: Response) => {
    const userId = req.session?.userId || "1"; // Default to user 1 for demo

    const platforms = ['linkedin', 'google', 'bing', 'yahoo'];
    const complianceData: any = {};

    platforms.forEach(platform => {
      const stats = complianceMiddleware.getUsageStats(platform, userId);
      const recommendations = complianceMiddleware.getComplianceRecommendations(platform, userId);
      
      complianceData[platform] = {
        ...stats,
        recommendations,
        compliant: stats ? stats.percentage < 95 : true
      };
    });

    res.json({
      userId,
      timestamp: new Date().toISOString(),
      platforms: complianceData,
      overallCompliant: Object.values(complianceData).every((p: any) => p.compliant)
    });
  });

  // Get platform-specific compliance details
  app.get("/api/compliance/:platform", (req: Request, res: Response) => {
    const { platform } = req.params;
    const userId = req.session?.userId || "1";

    if (!['linkedin', 'google', 'bing', 'yahoo'].includes(platform)) {
      return res.status(400).json({ error: "Invalid platform" });
    }

    const stats = complianceMiddleware.getUsageStats(platform, userId);
    const recommendations = complianceMiddleware.getComplianceRecommendations(platform, userId);

    if (!stats) {
      return res.status(404).json({ error: "Platform not configured" });
    }

    res.json({
      platform,
      userId,
      usage: stats,
      recommendations,
      compliant: stats.percentage < 95,
      warnings: stats.percentage >= 85 ? [`High usage detected for ${platform}`] : [],
      timestamp: new Date().toISOString()
    });
  });

  // Reset platform usage (for testing/admin purposes)
  app.post("/api/compliance/:platform/reset", (req: Request, res: Response) => {
    const { platform } = req.params;
    const userId = req.session?.userId || "1";

    if (!['linkedin', 'google', 'bing', 'yahoo'].includes(platform)) {
      return res.status(400).json({ error: "Invalid platform" });
    }

    // In a real implementation, this would be restricted to admins
    // For now, we'll allow it for testing purposes
    const key = `${platform}:${userId}`;
    delete (complianceMiddleware as any).rateLimitStore[key];

    res.json({
      message: `Usage reset for ${platform}`,
      platform,
      userId,
      timestamp: new Date().toISOString()
    });
  });

  // Log compliance event (for audit trail)
  app.post("/api/compliance/log", (req: Request, res: Response) => {
    const { platform, event, details } = req.body;
    const userId = req.session?.userId || "1";

    // In production, this would save to a database
    console.log(`[COMPLIANCE LOG] User: ${userId}, Platform: ${platform}, Event: ${event}, Details:`, details);

    res.json({
      message: "Event logged successfully",
      timestamp: new Date().toISOString(),
      userId,
      platform,
      event
    });
  });
}