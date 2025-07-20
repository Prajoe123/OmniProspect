import { 
  users, 
  searchResults, 
  prospects, 
  workflows, 
  apiUsage, 
  platformConnections,
  type User, 
  type InsertUser,
  type SearchResult,
  type InsertSearchResult,
  type Prospect,
  type InsertProspect,
  type Workflow,
  type InsertWorkflow,
  type ApiUsage,
  type PlatformConnection
} from "@shared/schema";
import { eq, desc, and, gte, sql } from "drizzle-orm";

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Search methods
  createSearchResult(searchResult: InsertSearchResult): Promise<SearchResult>;
  getSearchResults(userId: number, limit?: number): Promise<SearchResult[]>;
  getSearchResultById(id: number): Promise<SearchResult | undefined>;

  // Prospect methods
  createProspect(prospect: InsertProspect): Promise<Prospect>;
  getProspects(userId: number, limit?: number): Promise<Prospect[]>;
  getProspectById(id: number): Promise<Prospect | undefined>;
  updateProspect(id: number, updates: Partial<Prospect>): Promise<Prospect | undefined>;

  // Workflow methods
  createWorkflow(workflow: InsertWorkflow): Promise<Workflow>;
  getWorkflows(userId: number): Promise<Workflow[]>;
  getWorkflowById(id: number): Promise<Workflow | undefined>;
  updateWorkflow(id: number, updates: Partial<Workflow>): Promise<Workflow | undefined>;

  // Analytics methods
  getApiUsage(userId: number, days?: number): Promise<ApiUsage[]>;
  trackApiUsage(usage: Partial<ApiUsage>): Promise<ApiUsage>;
  getPlatformConnections(userId: number): Promise<PlatformConnection[]>;
  getProspectStats(userId: number): Promise<{
    total: number;
    thisMonth: number;
    conversionRate: string;
  }>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User> = new Map();
  private searchResults: Map<number, SearchResult> = new Map();
  private prospects: Map<number, Prospect> = new Map();
  private workflows: Map<number, Workflow> = new Map();
  private apiUsage: Map<number, ApiUsage> = new Map();
  private platformConnections: Map<number, PlatformConnection> = new Map();
  private currentId: { [key: string]: number } = {
    users: 1,
    searchResults: 1,
    prospects: 1,
    workflows: 1,
    apiUsage: 1,
    platformConnections: 1,
  };

  constructor() {
    // Initialize with demo data for the platform overview
    this.initializeDemoData();
  }

  private initializeDemoData() {
    // Create demo user
    const demoUser: User = {
      id: 1,
      username: "demo",
      password: "demo",
      email: "demo@omniprospect.com",
      name: "Demo User",
      role: "admin",
      createdAt: new Date(),
    };
    this.users.set(1, demoUser);
    this.currentId.users = 2;

    // Create platform connections - only LinkedIn and search engines
    const platforms = [
      { platform: "linkedin", status: "connected", lastSync: new Date(Date.now() - 2 * 60 * 1000) },
      { platform: "google", status: "connected", lastSync: new Date(Date.now() - 5 * 60 * 1000) },
      { platform: "bing", status: "connected", lastSync: new Date(Date.now() - 10 * 60 * 1000) },
      { platform: "yahoo", status: "setup_required", lastSync: null },
    ];

    platforms.forEach((platform, index) => {
      const connection: PlatformConnection = {
        id: index + 1,
        userId: 1,
        platform: platform.platform,
        status: platform.status as "connected",
        lastSync: platform.lastSync,
        syncData: null,
        createdAt: new Date(),
      };
      this.platformConnections.set(index + 1, connection);
    });
    this.currentId.platformConnections = platforms.length + 1;

    // Create demo prospects
    for (let i = 0; i < 50; i++) {
      const prospect: Prospect = {
        id: i + 1,
        userId: 1,
        name: `Prospect ${i + 1}`,
        email: `prospect${i + 1}@example.com`,
        company: `Company ${i + 1}`,
        title: "Software Engineer",
        linkedinUrl: null,
        twitterUrl: null,
        githubUrl: null,
        location: "San Francisco, CA",
        industry: "Technology",
        companySize: "51-200",
        source: "linkedin",
        enrichmentData: null,
        createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(),
      };
      this.prospects.set(i + 1, prospect);
    }
    this.currentId.prospects = 51;

    // Create demo workflows
    const demoWorkflow: Workflow = {
      id: 1,
      userId: 1,
      name: "LinkedIn → AI Enhancement → Email Campaign",
      description: "Automated prospect discovery and outreach",
      nodes: [
        { id: "1", type: "linkedin-search", position: { x: 100, y: 100 } },
        { id: "2", type: "ai-enhancement", position: { x: 300, y: 100 } },
        { id: "3", type: "email-campaign", position: { x: 500, y: 100 } },
      ],
      connections: [
        { source: "1", target: "2" },
        { source: "2", target: "3" },
      ],
      isActive: true,
      lastRun: new Date(Date.now() - 2 * 60 * 60 * 1000),
      createdAt: new Date(),
    };
    this.workflows.set(1, demoWorkflow);
    this.currentId.workflows = 2;
  }

  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.username === username);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentId.users++;
    const user: User = { 
      ...insertUser, 
      id, 
      role: "standard",
      createdAt: new Date() 
    };
    this.users.set(id, user);
    return user;
  }

  async createSearchResult(searchResult: InsertSearchResult): Promise<SearchResult> {
    const id = this.currentId.searchResults++;
    const result: SearchResult = {
      ...searchResult,
      id,
      createdAt: new Date(),
    };
    this.searchResults.set(id, result);
    return result;
  }

  async getSearchResults(userId: number, limit = 50): Promise<SearchResult[]> {
    return Array.from(this.searchResults.values())
      .filter(result => result.userId === userId)
      .sort((a, b) => b.createdAt!.getTime() - a.createdAt!.getTime())
      .slice(0, limit);
  }

  async getSearchResultById(id: number): Promise<SearchResult | undefined> {
    return this.searchResults.get(id);
  }

  async createProspect(prospect: InsertProspect): Promise<Prospect> {
    const id = this.currentId.prospects++;
    const newProspect: Prospect = {
      ...prospect,
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.prospects.set(id, newProspect);
    return newProspect;
  }

  async getProspects(userId: number, limit = 50): Promise<Prospect[]> {
    return Array.from(this.prospects.values())
      .filter(prospect => prospect.userId === userId)
      .sort((a, b) => b.createdAt!.getTime() - a.createdAt!.getTime())
      .slice(0, limit);
  }

  async getProspectById(id: number): Promise<Prospect | undefined> {
    return this.prospects.get(id);
  }

  async updateProspect(id: number, updates: Partial<Prospect>): Promise<Prospect | undefined> {
    const existing = this.prospects.get(id);
    if (!existing) return undefined;
    
    const updated = { ...existing, ...updates, updatedAt: new Date() };
    this.prospects.set(id, updated);
    return updated;
  }

  async createWorkflow(workflow: InsertWorkflow): Promise<Workflow> {
    const id = this.currentId.workflows++;
    const newWorkflow: Workflow = {
      ...workflow,
      id,
      createdAt: new Date(),
      lastRun: null,
    };
    this.workflows.set(id, newWorkflow);
    return newWorkflow;
  }

  async getWorkflows(userId: number): Promise<Workflow[]> {
    return Array.from(this.workflows.values())
      .filter(workflow => workflow.userId === userId)
      .sort((a, b) => b.createdAt!.getTime() - a.createdAt!.getTime());
  }

  async getWorkflowById(id: number): Promise<Workflow | undefined> {
    return this.workflows.get(id);
  }

  async updateWorkflow(id: number, updates: Partial<Workflow>): Promise<Workflow | undefined> {
    const existing = this.workflows.get(id);
    if (!existing) return undefined;
    
    const updated = { ...existing, ...updates };
    this.workflows.set(id, updated);
    return updated;
  }

  async getApiUsage(userId: number, days = 30): Promise<ApiUsage[]> {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    return Array.from(this.apiUsage.values())
      .filter(usage => usage.userId === userId && usage.date! >= cutoff)
      .sort((a, b) => b.date!.getTime() - a.date!.getTime());
  }

  async trackApiUsage(usage: Partial<ApiUsage>): Promise<ApiUsage> {
    const id = this.currentId.apiUsage++;
    const newUsage: ApiUsage = {
      id,
      userId: usage.userId!,
      service: usage.service!,
      endpoint: usage.endpoint || null,
      requestCount: usage.requestCount || 1,
      responseSize: usage.responseSize || null,
      cost: usage.cost || null,
      date: new Date(),
    };
    this.apiUsage.set(id, newUsage);
    return newUsage;
  }

  async getPlatformConnections(userId: number): Promise<PlatformConnection[]> {
    return Array.from(this.platformConnections.values())
      .filter(connection => connection.userId === userId);
  }

  async getProspectStats(userId: number): Promise<{
    total: number;
    thisMonth: number;
    conversionRate: string;
  }> {
    const userProspects = Array.from(this.prospects.values())
      .filter(prospect => prospect.userId === userId);
    
    const thisMonth = new Date();
    thisMonth.setDate(1);
    thisMonth.setHours(0, 0, 0, 0);
    
    const thisMonthProspects = userProspects.filter(
      prospect => prospect.createdAt! >= thisMonth
    );

    return {
      total: userProspects.length,
      thisMonth: thisMonthProspects.length,
      conversionRate: "18.3%", // This would be calculated based on actual conversion tracking
    };
  }
}

export const storage = new MemStorage();
