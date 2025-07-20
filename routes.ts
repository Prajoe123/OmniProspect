import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { searchQuerySchema, insertSearchResultSchema, insertProspectSchema } from "@shared/schema";
import { z } from "zod";
import { 
  complianceMiddleware, 
  linkedinRateLimit, 
  googleRateLimit, 
  bingRateLimit, 
  yahooRateLimit,
  trackLinkedInUsage,
  trackGoogleUsage,
  trackBingUsage,
  trackYahooUsage,
  validateCompliance
} from "./middleware/compliance";
import { registerComplianceRoutes } from "./routes/compliance";
import { 
  FallbackGoogleSearchService, 
  FallbackBingSearchService, 
  FallbackYahooSearchService, 
  FallbackLinkedInSearchService 
} from "./search-fallback";
import { 
  AdvancedGoogleSearchService,
  AdvancedBingSearchService,
  DuckDuckGoSearchService,
  YandexSearchService,
  SearchAggregator,
  SearchExporter
} from "./search-advanced";
import { advancedSearchQuerySchema } from "@shared/advanced-search-schema";

// Search API services
export interface SearchService {
  search(query: string, options?: any): Promise<any>;
}

class GoogleCustomSearchService implements SearchService {
  private apiKey: string;
  private searchEngineId: string;

  constructor() {
    this.apiKey = process.env.GOOGLE_API_KEY || process.env.GOOGLE_CUSTOM_SEARCH_API_KEY || "";
    this.searchEngineId = process.env.GOOGLE_SEARCH_ENGINE_ID || process.env.GOOGLE_CSE_ID || "";
  }

  async search(query: string, options: any = {}) {
    if (!this.apiKey || !this.searchEngineId) {
      throw new Error("Google Custom Search API key or Search Engine ID not configured");
    }

    const params = new URLSearchParams({
      key: this.apiKey,
      cx: this.searchEngineId,
      q: query,
      num: options.limit?.toString() || "10",
    });

    const response = await fetch(`https://www.googleapis.com/customsearch/v1?${params}`);
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Google Custom Search API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return {
      results: data.items || [],
      totalResults: parseInt(data.searchInformation?.totalResults || "0"),
      searchTime: parseFloat(data.searchInformation?.searchTime || "0"),
    };
  }
}

class BingWebSearchService implements SearchService {
  private apiKey: string;

  constructor() {
    this.apiKey = process.env.BING_SEARCH_API_KEY || process.env.AZURE_BING_SEARCH_KEY || "";
  }

  async search(query: string, options: any = {}) {
    if (!this.apiKey) {
      throw new Error("Bing Web Search API key not configured");
    }

    const params = new URLSearchParams({
      q: query,
      count: options.limit?.toString() || "10",
      mkt: "en-US",
      safesearch: "Moderate",
    });

    const response = await fetch(`https://api.bing.microsoft.com/v7.0/search?${params}`, {
      headers: {
        "Ocp-Apim-Subscription-Key": this.apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Bing Web Search API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return {
      results: data.webPages?.value || [],
      totalResults: parseInt(data.webPages?.totalEstimatedMatches || "0"),
      searchTime: 0, // Bing doesn't provide search time
    };
  }
}

class YahooSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // Yahoo search through web scraping (respecting robots.txt)
    const encodedQuery = encodeURIComponent(query);
    const url = `https://search.yahoo.com/search?p=${encodedQuery}&n=${options.limit || 10}`;
    
    try {
      // Note: This would require proper web scraping implementation
      // For now, return a structured response indicating Yahoo integration
      return {
        results: [],
        totalResults: 0,
        searchTime: 0,
        note: "Yahoo search integration - requires web scraping implementation"
      };
    } catch (error) {
      throw new Error(`Yahoo search error: ${error}`);
    }
  }
}

class LinkedInSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // LinkedIn public profile search (compliance-focused)
    try {
      // Note: This would require proper LinkedIn scraping with rate limiting
      // Must respect LinkedIn's fair use guidelines: <100 profiles/day for free accounts
      return {
        results: [],
        totalResults: 0,
        searchTime: 0,
        note: "LinkedIn search integration - requires compliant scraping implementation with rate limits"
      };
    } catch (error) {
      throw new Error(`LinkedIn search error: ${error}`);
    }
  }
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Use fallback services for testing when API keys aren't available
  const googleSearch = process.env.GOOGLE_CUSTOM_SEARCH_API_KEY && process.env.GOOGLE_SEARCH_ENGINE_ID 
    ? new GoogleCustomSearchService() 
    : new FallbackGoogleSearchService();
  
  const bingSearch = process.env.BING_SEARCH_API_KEY 
    ? new BingWebSearchService() 
    : new FallbackBingSearchService();
  
  const yahooSearch = new FallbackYahooSearchService(); // Always use fallback for Yahoo
  const linkedinSearch = new FallbackLinkedInSearchService(); // Always use fallback for LinkedIn
  
  // Advanced search services
  const advancedGoogleSearch = new AdvancedGoogleSearchService();
  const advancedBingSearch = new AdvancedBingSearchService();
  const duckduckgoSearch = new DuckDuckGoSearchService();
  const yandexSearch = new YandexSearchService();
  const searchAggregator = new SearchAggregator();

  // Advanced multi-platform search endpoint
  app.post("/api/search/advanced", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const searchData = advancedSearchQuerySchema.parse(req.body);
      
      let platforms = searchData.platforms;
      if (platforms.includes("all")) {
        platforms = ["google", "bing", "duckduckgo", "yandex"];
      }

      const aggregatedResults = await searchAggregator.aggregateResults(
        searchData.query, 
        platforms, 
        { 
          operators: searchData.operators,
          limit: searchData.limit 
        }
      );

      // Save to search history if requested
      if (searchData.saveQuery && searchData.queryName) {
        // In a real app, save the query to database
        console.log(`Saving query: ${searchData.queryName} - ${searchData.query}`);
      }

      // Export if format specified
      let exportData = null;
      if (searchData.exportFormat) {
        switch (searchData.exportFormat) {
          case 'json':
            exportData = SearchExporter.exportToJSON(aggregatedResults);
            break;
          case 'csv':
            exportData = SearchExporter.exportToCSV(aggregatedResults);
            break;
          case 'pdf':
            exportData = SearchExporter.generatePDFData(aggregatedResults);
            break;
        }
      }

      // Store search result in database
      const searchResult = await storage.createSearchResult({
        userId,
        query: searchData.query,
        source: platforms.join(','),
        results: { 
          data: aggregatedResults.results, 
          errors: [],
          aggregated: true,
          comparison: aggregatedResults.comparison
        },
        metadata: {
          platforms,
          operators: searchData.operators,
          limit: searchData.limit,
          exportFormat: searchData.exportFormat,
          timestamp: new Date().toISOString(),
        },
      });

      res.json({
        id: searchResult.id,
        ...aggregatedResults,
        exportData,
        saved: !!searchData.saveQuery
      });

    } catch (error) {
      console.error("Advanced search error:", error);
      res.status(400).json({ 
        message: error instanceof Error ? error.message : "Advanced search failed"
      });
    }
  });

  // Search with specific boolean operators
  app.post("/api/search/boolean", async (req, res) => {
    try {
      const { query, operator, terms, platform = "google" } = req.body;
      
      let booleanQuery = "";
      switch (operator) {
        case "AND":
          booleanQuery = terms.join(" AND ");
          break;
        case "OR":
          booleanQuery = terms.join(" OR ");
          break;
        case "NOT":
          booleanQuery = `${terms[0]} NOT ${terms.slice(1).join(" NOT ")}`;
          break;
        case "NEAR":
          booleanQuery = `${terms[0]} NEAR:5 ${terms[1]}`;
          break;
        default:
          booleanQuery = query;
      }

      const service = platform === "bing" ? advancedBingSearch : advancedGoogleSearch;
      const results = await service.search(booleanQuery, { limit: 10 });

      res.json({
        query: booleanQuery,
        operator,
        platform,
        results,
        originalTerms: terms
      });

    } catch (error) {
      console.error("Boolean search error:", error);
      res.status(400).json({ 
        message: error instanceof Error ? error.message : "Boolean search failed"
      });
    }
  });

  // Export search results
  app.get("/api/search/:id/export/:format", async (req, res) => {
    try {
      const { id, format } = req.params;
      const searchResult = await storage.getSearchResultById(parseInt(id));
      
      if (!searchResult) {
        return res.status(404).json({ message: "Search result not found" });
      }

      let exportData;
      let contentType;
      let filename;

      switch (format) {
        case 'json':
          exportData = SearchExporter.exportToJSON(searchResult);
          contentType = 'application/json';
          filename = `search-results-${id}.json`;
          break;
        case 'csv':
          exportData = SearchExporter.exportToCSV(searchResult);
          contentType = 'text/csv';
          filename = `search-results-${id}.csv`;
          break;
        case 'pdf':
          exportData = JSON.stringify(SearchExporter.generatePDFData(searchResult));
          contentType = 'application/json'; // PDF data for frontend to process
          filename = `search-results-${id}-pdf.json`;
          break;
        default:
          return res.status(400).json({ message: "Unsupported export format" });
      }

      res.setHeader('Content-Type', contentType);
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
      res.send(exportData);

    } catch (error) {
      console.error("Export error:", error);
      res.status(500).json({ message: "Export failed" });
    }
  });

  // Search tutorials and examples
  app.get("/api/search/tutorials", async (req, res) => {
    try {
      const tutorials = [
        {
          id: "basic-search",
          title: "Basic Search Techniques",
          description: "Learn fundamental search strategies across multiple platforms",
          example: "software engineer San Francisco",
          category: "basic",
          difficulty: "beginner",
          searchQuery: "software engineer San Francisco",
          expectedResults: "Job listings and profiles for software engineers in San Francisco",
          tips: [
            "Use specific job titles for better results",
            "Include location for geographic targeting",
            "Try variations of job titles"
          ]
        },
        {
          id: "boolean-operators",
          title: "Boolean Search Operators",
          description: "Master AND, OR, NOT operators for precise searches",
          example: "(software engineer OR developer) AND (startup OR tech company) NOT intern",
          category: "boolean",
          difficulty: "intermediate",
          searchQuery: "(software engineer OR developer) AND (startup OR tech company) NOT intern",
          expectedResults: "Senior software professionals at tech companies, excluding internships",
          tips: [
            "Use parentheses to group terms",
            "AND narrows results, OR expands them",
            "NOT excludes unwanted terms"
          ]
        },
        {
          id: "site-operator",
          title: "Site-Specific Search",
          description: "Search within specific websites or domains",
          example: "site:linkedin.com software engineer",
          category: "operators",
          difficulty: "intermediate",
          searchQuery: "site:linkedin.com software engineer",
          expectedResults: "Software engineer profiles specifically from LinkedIn",
          tips: [
            "Use site: to search within specific domains",
            "Works across all major search engines",
            "Combine with other operators for precision"
          ]
        },
        {
          id: "filetype-search",
          title: "File Type Search",
          description: "Find specific document types like PDFs, presentations",
          example: "filetype:pdf machine learning research",
          category: "operators",
          difficulty: "intermediate",
          searchQuery: "filetype:pdf machine learning research",
          expectedResults: "PDF documents about machine learning research",
          tips: [
            "Common file types: pdf, doc, ppt, xls",
            "Great for finding research papers and reports",
            "Combine with site: for targeted searches"
          ]
        },
        {
          id: "advanced-combinations",
          title: "Advanced Operator Combinations",
          description: "Combine multiple operators for powerful searches",
          example: "intitle:\"VP Engineering\" site:linkedin.com (startup OR \"series A\")",
          category: "advanced",
          difficulty: "advanced",
          searchQuery: "intitle:\"VP Engineering\" site:linkedin.com (startup OR \"series A\")",
          expectedResults: "VP Engineering profiles at startups on LinkedIn",
          tips: [
            "intitle: searches page titles",
            "Use quotes for exact phrases",
            "Combine site:, intitle:, and boolean operators"
          ]
        }
      ];

      const { category, difficulty } = req.query;
      let filteredTutorials = tutorials;

      if (category) {
        filteredTutorials = filteredTutorials.filter(t => t.category === category);
      }
      if (difficulty) {
        filteredTutorials = filteredTutorials.filter(t => t.difficulty === difficulty);
      }

      res.json({
        tutorials: filteredTutorials,
        categories: ["basic", "boolean", "operators", "advanced", "export"],
        difficulties: ["beginner", "intermediate", "advanced"],
        totalTutorials: filteredTutorials.length
      });

    } catch (error) {
      console.error("Tutorials error:", error);
      res.status(500).json({ message: "Failed to fetch tutorials" });
    }
  });

  // Search endpoints
  app.post("/api/search", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const searchData = searchQuerySchema.parse(req.body);
      
      const results = [];
      const errors = [];

      // Perform searches based on source
      if (searchData.source === "all" || searchData.source === "google") {
        try {
          const googleResults = await googleSearch.search(searchData.query, { limit: searchData.limit });
          results.push({
            source: "google",
            ...googleResults,
          });
          
          // Track API usage
          await storage.trackApiUsage({
            userId,
            service: "google",
            endpoint: "customsearch",
            requestCount: 1,
          });
        } catch (error) {
          errors.push({ source: "google", error: (error as Error).message });
        }
      }

      if (searchData.source === "all" || searchData.source === "bing") {
        try {
          const bingResults = await bingSearch.search(searchData.query, { limit: searchData.limit });
          results.push({
            source: "bing",
            ...bingResults,
          });
          
          await storage.trackApiUsage({
            userId,
            service: "bing",
            endpoint: "websearch",
            requestCount: 1,
          });
        } catch (error) {
          errors.push({ source: "bing", error: (error as Error).message });
        }
      }

      if (searchData.source === "all" || searchData.source === "yahoo") {
        try {
          const yahooResults = await yahooSearch.search(searchData.query, { limit: searchData.limit });
          results.push({
            source: "yahoo",
            ...yahooResults,
          });
          
          await storage.trackApiUsage({
            userId,
            service: "yahoo",
            endpoint: "websearch",
            requestCount: 1,
          });
        } catch (error) {
          errors.push({ source: "yahoo", error: (error as Error).message });
        }
      }

      if (searchData.source === "all" || searchData.source === "linkedin") {
        try {
          const linkedinResults = await linkedinSearch.search(searchData.query, { limit: searchData.limit });
          results.push({
            source: "linkedin",
            ...linkedinResults,
          });
          
          await storage.trackApiUsage({
            userId,
            service: "linkedin",
            endpoint: "profile_search",
            requestCount: 1,
          });
        } catch (error) {
          errors.push({ source: "linkedin", error: (error as Error).message });
        }
      }

      // Store search results
      const searchResult = await storage.createSearchResult({
        userId,
        query: searchData.query,
        source: searchData.source,
        results: { data: results, errors },
        metadata: {
          filters: searchData.filters,
          limit: searchData.limit,
          timestamp: new Date().toISOString(),
        },
      });

      res.json({
        id: searchResult.id,
        results,
        errors,
        totalSources: results.length,
        query: searchData.query,
      });
    } catch (error) {
      console.error("Search error:", error);
      res.status(400).json({ 
        message: error instanceof Error ? error.message : "Search failed"
      });
    }
  });

  // Get search history
  app.get("/api/search/history", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const limit = parseInt(req.query.limit as string) || 50;
      
      const history = await storage.getSearchResults(userId, limit);
      res.json(history);
    } catch (error) {
      console.error("Search history error:", error);
      res.status(500).json({ message: "Failed to fetch search history" });
    }
  });

  // Dashboard stats
  app.get("/api/dashboard/stats", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      
      const prospectStats = await storage.getProspectStats(userId);
      const workflows = await storage.getWorkflows(userId);
      const platformConnections = await storage.getPlatformConnections(userId);
      const apiUsage = await storage.getApiUsage(userId, 30);
      
      res.json({
        prospects: prospectStats,
        workflows: {
          total: workflows.length,
          active: workflows.filter(w => w.isActive).length,
        },
        platforms: {
          total: platformConnections.length,
          connected: platformConnections.filter(p => p.status === "connected").length,
        },
        apiUsage: {
          totalRequests: apiUsage.reduce((sum, usage) => sum + (usage.requestCount || 0), 0),
          services: apiUsage.reduce((acc, usage) => {
            acc[usage.service] = (acc[usage.service] || 0) + (usage.requestCount || 0);
            return acc;
          }, {} as Record<string, number>),
        },
      });
    } catch (error) {
      console.error("Dashboard stats error:", error);
      res.status(500).json({ message: "Failed to fetch dashboard stats" });
    }
  });

  // Platform connections
  app.get("/api/platforms", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const connections = await storage.getPlatformConnections(userId);
      res.json(connections);
    } catch (error) {
      console.error("Platform connections error:", error);
      res.status(500).json({ message: "Failed to fetch platform connections" });
    }
  });

  // Prospects endpoints
  app.get("/api/prospects", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const limit = parseInt(req.query.limit as string) || 50;
      
      const prospects = await storage.getProspects(userId, limit);
      res.json(prospects);
    } catch (error) {
      console.error("Prospects error:", error);
      res.status(500).json({ message: "Failed to fetch prospects" });
    }
  });

  app.post("/api/prospects", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const prospectData = insertProspectSchema.parse({ ...req.body, userId });
      
      const prospect = await storage.createProspect(prospectData);
      res.json(prospect);
    } catch (error) {
      console.error("Create prospect error:", error);
      res.status(400).json({ 
        message: error instanceof Error ? error.message : "Failed to create prospect"
      });
    }
  });

  // Workflows endpoints
  app.get("/api/workflows", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const workflows = await storage.getWorkflows(userId);
      res.json(workflows);
    } catch (error) {
      console.error("Workflows error:", error);
      res.status(500).json({ message: "Failed to fetch workflows" });
    }
  });

  // API usage analytics
  app.get("/api/analytics/usage", async (req, res) => {
    try {
      const userId = 1; // In a real app, get from authenticated session
      const days = parseInt(req.query.days as string) || 30;
      
      const usage = await storage.getApiUsage(userId, days);
      res.json(usage);
    } catch (error) {
      console.error("API usage analytics error:", error);
      res.status(500).json({ message: "Failed to fetch API usage analytics" });
    }
  });

  // Register compliance routes
  registerComplianceRoutes(app);

  const httpServer = createServer(app);
  return httpServer;
}
