// Fallback search implementations for testing without API keys
import { SearchService } from './routes';

export class FallbackGoogleSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // Simulate Google search results for testing
    const mockResults = [
      {
        title: `${query} - Google Search Result 1`,
        link: `https://example1.com/search?q=${encodeURIComponent(query)}`,
        snippet: `This is a sample search result for "${query}". In a real implementation, this would come from Google Custom Search API.`,
        displayLink: "example1.com"
      },
      {
        title: `${query} - Google Search Result 2`,
        link: `https://example2.com/results/${encodeURIComponent(query)}`,
        snippet: `Another sample result showing how the search system would work with real data from Google's API.`,
        displayLink: "example2.com"
      },
      {
        title: `${query} - Google Search Result 3`,
        link: `https://example3.com/info?search=${encodeURIComponent(query)}`,
        snippet: `Third sample result demonstrating the structure of search results from Google Custom Search.`,
        displayLink: "example3.com"
      }
    ];

    // Add slight delay to simulate real API call
    await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));

    return {
      results: mockResults.slice(0, options.limit || 10),
      totalResults: mockResults.length,
      searchTime: Math.random() * 500 + 100
    };
  }
}

export class FallbackBingSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // Simulate Bing search results for testing
    const mockResults = [
      {
        name: `${query} - Bing Search Result 1`,
        url: `https://bing-example1.com/search?q=${encodeURIComponent(query)}`,
        snippet: `This is a sample Bing search result for "${query}". Real implementation would use Bing Web Search API.`,
        displayUrl: "bing-example1.com"
      },
      {
        name: `${query} - Bing Search Result 2`,
        url: `https://bing-example2.com/results/${encodeURIComponent(query)}`,
        snippet: `Another Bing result showing the search functionality with proper rate limiting and compliance monitoring.`,
        displayUrl: "bing-example2.com"
      },
      {
        name: `${query} - Bing Search Result 3`,
        url: `https://bing-example3.com/info?q=${encodeURIComponent(query)}`,
        snippet: `Third Bing result demonstrating how the system handles multiple search sources simultaneously.`,
        displayUrl: "bing-example3.com"
      }
    ];

    // Add slight delay to simulate real API call
    await new Promise(resolve => setTimeout(resolve, 150 + Math.random() * 250));

    return {
      results: mockResults.slice(0, options.limit || 10),
      totalResults: mockResults.length,
      searchTime: Math.random() * 600 + 150
    };
  }
}

export class FallbackYahooSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // Simulate Yahoo search results for testing
    const mockResults = [
      {
        title: `${query} - Yahoo Search Result 1`,
        url: `https://yahoo-example1.com/search?p=${encodeURIComponent(query)}`,
        abstract: `Sample Yahoo search result for "${query}". This demonstrates web scraping with proper robots.txt compliance.`,
        clickUrl: `https://yahoo-example1.com/search?p=${encodeURIComponent(query)}`
      },
      {
        title: `${query} - Yahoo Search Result 2`,
        url: `https://yahoo-example2.com/results/${encodeURIComponent(query)}`,
        abstract: `Another Yahoo result showing rate-limited web scraping with 1-2 second delays between requests.`,
        clickUrl: `https://yahoo-example2.com/results/${encodeURIComponent(query)}`
      }
    ];

    // Add longer delay to simulate Yahoo's rate limiting requirements
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));

    return {
      results: mockResults.slice(0, options.limit || 5),
      totalResults: mockResults.length,
      searchTime: Math.random() * 1200 + 800
    };
  }
}

export class FallbackLinkedInSearchService implements SearchService {
  async search(query: string, options: any = {}) {
    // Generate professional profile placeholders based on search query
    const profileTitles = ['Senior', 'Lead', 'Principal', 'Director', 'VP', 'Manager'];
    const companies = ['Tech Solutions Inc', 'Innovation Labs', 'Global Enterprises', 'Digital Dynamics', 'Future Systems'];
    const locations = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Boston, MA'];
    
    const mockResults = Array.from({ length: 3 }, (_, index) => {
      const title = profileTitles[index % profileTitles.length];
      const company = companies[index % companies.length];
      const location = locations[index % locations.length];
      
      return {
        name: `${title} ${query} Professional`,
        headline: `${title} ${query} at ${company}`,
        location: location,
        profileUrl: `https://linkedin.com/in/professional-${index + 1}-${query.toLowerCase().replace(/\s+/g, '-')}`,
        summary: `Experienced ${query} professional with expertise in leading teams and driving business results at ${company}.`,
        connections: `${Math.floor(Math.random() * 900 + 500)}+`
      };
    });

    // Add delay to simulate LinkedIn's 2-3 second requirement
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1000));

    return {
      results: mockResults.slice(0, options.limit || 10),
      totalResults: mockResults.length,
      searchTime: Math.random() * 1500 + 2000
    };
  }
}