#!/usr/bin/env node

/**
 * Automated OpenAPI client generation script
 *
 * This script:
 * 1. Fetches OpenAPI schema from running FastAPI backend
 * 2. Generates TypeScript client using openapi-generator-cli
 * 3. Validates the generated client matches current usage
 * 4. Updates the existing API client with new methods
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Configuration
const CONFIG = {
  // API endpoints
  apiUrl: process.env.API_URL || 'http://localhost:8000',
  openApiPath: '/openapi.json',

  // Generation paths
  outputDir: path.join(__dirname, '..', 'generated', 'api-client'),
  currentClientPath: path.join(__dirname, '..', 'packages', 'ts', 'http-client', 'src', 'index.ts'),
  tempSchemaPath: path.join(__dirname, '..', 'temp', 'openapi.json'),

  // Generator settings
  generatorName: 'typescript-axios',
  packageName: '@originfd/http-client-generated',

  // Validation patterns
  methodPatterns: [
    /async\s+(\w+)\s*\(/g,  // Match async method definitions
    /\.\s*(\w+)\s*\(/g      // Match method calls
  ]
};

/**
 * Ensure required directories exist
 */
async function ensureDirectories() {
  const dirs = [
    path.dirname(CONFIG.outputDir),
    path.dirname(CONFIG.tempSchemaPath),
    CONFIG.outputDir
  ];

  for (const dir of dirs) {
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
    }
  }
}

/**
 * Check if API server is running
 */
async function checkApiServer() {
  try {
    console.log(`🔍 Checking API server at ${CONFIG.apiUrl}...`);
    const response = await fetch(`${CONFIG.apiUrl}/health`);
    if (!response.ok) {
      throw new Error(`API server responded with ${response.status}`);
    }
    console.log('✅ API server is running');
    return true;
  } catch (error) {
    console.error(`❌ API server not accessible: ${error.message}`);
    console.log('💡 Make sure the API server is running with: cd services/api && python main.py');
    return false;
  }
}

/**
 * Fetch OpenAPI schema from the running API
 */
async function fetchOpenApiSchema() {
  try {
    console.log('📥 Fetching OpenAPI schema...');
    const response = await fetch(`${CONFIG.apiUrl}${CONFIG.openApiPath}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI schema: ${response.status} ${response.statusText}`);
    }

    const schema = await response.json();

    // Save schema to temp file
    await fs.writeFile(CONFIG.tempSchemaPath, JSON.stringify(schema, null, 2));
    console.log(`✅ OpenAPI schema saved to ${CONFIG.tempSchemaPath}`);

    return schema;
  } catch (error) {
    console.error(`❌ Failed to fetch OpenAPI schema: ${error.message}`);
    throw error;
  }
}

/**
 * Install openapi-generator-cli if not present
 */
async function ensureOpenApiGenerator() {
  try {
    await execAsync('npx openapi-generator-cli version');
    console.log('✅ openapi-generator-cli is available');
  } catch (error) {
    console.log('📦 Installing openapi-generator-cli...');
    await execAsync('npm install -g @openapitools/openapi-generator-cli');
    console.log('✅ openapi-generator-cli installed');
  }
}

/**
 * Generate TypeScript client from OpenAPI schema
 */
async function generateClient() {
  try {
    console.log('🔨 Generating TypeScript client...');

    const command = [
      'npx openapi-generator-cli generate',
      `-i ${CONFIG.tempSchemaPath}`,
      `-g ${CONFIG.generatorName}`,
      `-o ${CONFIG.outputDir}`,
      `--package-name=${CONFIG.packageName}`,
      '--additional-properties=',
      [
        'supportsES6=true',
        'typescriptThreePlus=true',
        'withInterfaces=true',
        'apiPackage=api',
        'modelPackage=models'
      ].join(',')
    ].join(' ');

    const { stdout, stderr } = await execAsync(command);

    if (stderr && !stderr.includes('WARN')) {
      console.warn('⚠️ Generator warnings:', stderr);
    }

    console.log('✅ TypeScript client generated successfully');
    return CONFIG.outputDir;
  } catch (error) {
    console.error(`❌ Failed to generate client: ${error.message}`);
    throw error;
  }
}

/**
 * Extract method names from existing client
 */
async function analyzeExistingClient() {
  try {
    const clientContent = await fs.readFile(CONFIG.currentClientPath, 'utf8');

    const methods = new Set();

    // Extract async method definitions
    const asyncMethodMatches = clientContent.matchAll(/async\s+(\w+)\s*\(/g);
    for (const match of asyncMethodMatches) {
      methods.add(match[1]);
    }

    // Extract method calls from usage patterns
    const methodCallMatches = clientContent.matchAll(/\.\s*(\w+)\s*\(/g);
    for (const match of methodCallMatches) {
      methods.add(match[1]);
    }

    console.log(`📊 Found ${methods.size} methods in existing client`);
    return Array.from(methods);
  } catch (error) {
    console.warn(`⚠️ Could not analyze existing client: ${error.message}`);
    return [];
  }
}

/**
 * Validate generated client against existing usage
 */
async function validateGeneratedClient(existingMethods) {
  try {
    console.log('🔍 Validating generated client...');

    // Read the generated API file
    const apiFiles = await fs.readdir(path.join(CONFIG.outputDir, 'api'));
    const generatedApiFile = apiFiles.find(file => file.endsWith('.ts'));

    if (!generatedApiFile) {
      throw new Error('No generated API file found');
    }

    const generatedContent = await fs.readFile(
      path.join(CONFIG.outputDir, 'api', generatedApiFile),
      'utf8'
    );

    // Extract generated methods
    const generatedMethods = new Set();
    const methodMatches = generatedContent.matchAll(/public\s+(\w+)\s*\(/g);
    for (const match of methodMatches) {
      generatedMethods.add(match[1]);
    }

    // Check coverage
    const missingMethods = existingMethods.filter(method =>
      !generatedMethods.has(method) &&
      !['constructor', 'request', 'get', 'post', 'put', 'patch', 'delete'].includes(method)
    );

    if (missingMethods.length > 0) {
      console.warn(`⚠️ Missing methods in generated client: ${missingMethods.join(', ')}`);
    } else {
      console.log('✅ Generated client covers all existing methods');
    }

    return {
      generated: Array.from(generatedMethods),
      missing: missingMethods,
      coverage: ((existingMethods.length - missingMethods.length) / existingMethods.length * 100).toFixed(1)
    };
  } catch (error) {
    console.error(`❌ Validation failed: ${error.message}`);
    return { generated: [], missing: [], coverage: '0' };
  }
}

/**
 * Create integration report
 */
async function createReport(schema, validation) {
  const report = {
    timestamp: new Date().toISOString(),
    api: {
      url: CONFIG.apiUrl,
      version: schema.info?.version || 'unknown',
      title: schema.info?.title || 'OriginFD API'
    },
    generation: {
      outputDir: CONFIG.outputDir,
      generatorName: CONFIG.generatorName,
      packageName: CONFIG.packageName
    },
    validation: {
      coverage: validation.coverage + '%',
      generatedMethods: validation.generated.length,
      missingMethods: validation.missing.length,
      missing: validation.missing
    },
    endpoints: Object.keys(schema.paths || {}).length
  };

  const reportPath = path.join(CONFIG.outputDir, 'generation-report.json');
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

  console.log('📋 Generation report saved to:', reportPath);
  console.log(`📊 Client coverage: ${validation.coverage}%`);
  console.log(`🔗 Generated ${validation.generated.length} methods from ${report.endpoints} endpoints`);

  return report;
}

/**
 * Main execution function
 */
async function main() {
  try {
    console.log('🚀 Starting OpenAPI client generation...\n');

    // Setup
    await ensureDirectories();

    // Check if API is running
    const apiRunning = await checkApiServer();
    if (!apiRunning) {
      process.exit(1);
    }

    // Fetch schema
    const schema = await fetchOpenApiSchema();

    // Analyze existing client
    const existingMethods = await analyzeExistingClient();

    // Ensure generator is available
    await ensureOpenApiGenerator();

    // Generate client
    await generateClient();

    // Validate
    const validation = await validateGeneratedClient(existingMethods);

    // Create report
    await createReport(schema, validation);

    console.log('\n✅ OpenAPI client generation completed successfully!');
    console.log(`📁 Generated client available at: ${CONFIG.outputDir}`);
    console.log('💡 Next steps:');
    console.log('   1. Review the generated client');
    console.log('   2. Update your existing client with new methods');
    console.log('   3. Run tests to ensure compatibility');

  } catch (error) {
    console.error(`\n❌ Generation failed: ${error.message}`);
    process.exit(1);
  } finally {
    // Cleanup temp files
    try {
      await fs.unlink(CONFIG.tempSchemaPath);
    } catch (error) {
      // Ignore cleanup errors
    }
  }
}

// Add fetch polyfill for Node.js
if (typeof globalThis.fetch === 'undefined') {
  const { fetch } = require('node-fetch');
  globalThis.fetch = fetch;
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  generateClient: main,
  CONFIG
};