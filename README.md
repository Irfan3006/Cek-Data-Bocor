# Data Breach Checker

A modern, fast, secure, and deployment-ready web application to detect whether an email address has been compromised in public data breach incidents. The application is tailored for Indonesian users, featuring a 100 percent Indonesian user interface.

The application utilizes a clean architecture combining high-performance technologies:
* **Frontend**: Astro, TypeScript, Tailwind CSS (utilizing Static Site Generation for instant load times and a Largest Contentful Paint under 2 seconds).
* **Backend**: Python 3.13, FastAPI, Uvicorn, HTTPX, and Async (utilizing custom risk scoring and a rule-based mitigation recommendation engine).
* **Deployment**: Vercel Serverless (Astro static edge hosting and FastAPI Serverless Functions).

***

## Key Features

1. **Fast and Lightweight Examination**: Direct integration with a public data breach API database with optimal client-side rendering.
2. **Custom Risk Evaluation**: An algorithm calculating risk scores from 0 to 100 and risk categories (Safe, Low, Moderate, High, Critical).
3. **Intelligent Recommendation Engine**: Specific security mitigation actions provided in Indonesian, tailored to the type of compromise (such as password, telephone number, username, new credentials, or old credentials).
4. **Protection and Security**:
   * A thread-safe in-memory cache with a 10-minute Time-To-Live (TTL) to reduce redundant external API requests.
   * IP-based rate limiting (maximum of 10 requests per minute per IP address) to prevent API exploitation.
   * Comprehensive security headers including Content Security Policy (CSP), Strict Transport Security (HSTS), X-Frame-Options, and X-Content-Type-Options.
   * Safe error handling that prevents internal system stack traces from being exposed to the client.
5. **Accessibility (A11y)**: Built with full keyboard navigation support, semantic HTML elements, high-contrast focus rings, and Accessible Rich Internet Applications (ARIA) attributes.
6. **SEO Optimization**: Fully integrated JSON-LD structured schema metadata (WebSite and FAQPage), robots.txt, sitemap.xml, comprehensive Open Graph and Twitter Card tags, and Cumulative Layout Shift (CLS) values near zero.

***

## System Requirements

* **Python**: Version 3.13 or newer.
* **Node.js**: Version 18.x, 20.x, or newer.
* **Vercel CLI** (optional, for local deployment simulation).

***

## Local Execution Instructions

### 1. Repository Setup
Verify that you are in the workspace root directory. Copy the environment configuration file:
```bash
cp .env.example .env
```

### 2. Run the FastAPI Backend
1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS or Linux:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server using Uvicorn:
   ```bash
   uvicorn api.index:app --reload --port 8000
   ```
   *Note: The backend will be accessible at http://localhost:8000.*

### 3. Run the Astro Frontend
1. Open a new terminal session and install Node.js dependencies:
   ```bash
   npm install
   ```
2. Start the Astro development server:
   ```bash
   npm run dev
   ```
   *Note: The frontend will be accessible at http://localhost:4321.*

***

## Local Deployment Simulation Using Vercel CLI

To replicate the Vercel production environment locally, which automatically routes static frontend pages and serverless backend functions, use the Vercel CLI:

1. Install the Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```
2. Start the local simulation:
   ```bash
   vercel dev
   ```
   *Note: The Vercel CLI will build the frontend assets and run the FastAPI serverless functions under a single unified local address (typically http://localhost:3000).*

***

## Deploying to Vercel

The application is structured for zero-configuration deployment:
1. Connect this repository to your Vercel account.
2. Vercel will automatically identify the Astro framework.
3. Click the Deploy button. The serverless functions inside the `api/` directory will be built automatically using the Python runtime.

***

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

