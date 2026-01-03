/**
 * Vercel Edge Function for secure thesis generation via Perplexity API.
 * Password-protected to prevent unauthorized API usage.
 */

export const config = {
  runtime: 'edge',
};

interface ThesisRequest {
  ticker: string;
  company_name?: string;
  investor_names?: string[];
  password: string;
}

interface ThesisResponse {
  success: boolean;
  thesis?: string;
  error?: string;
  ticker?: string;
}

export default async function handler(request: Request): Promise<Response> {
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
  }

  // Only allow POST
  if (request.method !== 'POST') {
    return new Response(
      JSON.stringify({ success: false, error: 'Method not allowed' }),
      {
        status: 405,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }

  try {
    const body: ThesisRequest = await request.json();
    const { ticker, company_name, investor_names, password } = body;

    // Validate password
    const expectedPassword = process.env.THESIS_PASSWORD;
    if (!expectedPassword) {
      return new Response(
        JSON.stringify({ success: false, error: 'Server not configured' }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    if (password !== expectedPassword) {
      return new Response(
        JSON.stringify({ success: false, error: 'Invalid password' }),
        {
          status: 401,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    // Validate ticker
    if (!ticker) {
      return new Response(
        JSON.stringify({ success: false, error: 'Ticker is required' }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    // Get Perplexity API key
    const perplexityApiKey = process.env.PERPLEXITY_API_KEY;
    if (!perplexityApiKey) {
      return new Response(
        JSON.stringify({ success: false, error: 'Perplexity API not configured' }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    // Build the prompt
    const investorList = investor_names && investor_names.length > 0
      ? investor_names.slice(0, 5).join(', ')
      : 'value investors';

    const companyInfo = company_name ? `${company_name} (${ticker})` : ticker;

    const prompt = `Why might ${investorList} be buying ${companyInfo}? What's the investment thesis? Provide a concise answer in 2-3 lines maximum, focusing on the key bull case.`;

    // Call Perplexity API
    const perplexityResponse = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${perplexityApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.1-sonar-small-128k-online',
        messages: [
          {
            role: 'system',
            content: 'You are a concise financial analyst. Provide brief, actionable investment insights. Focus on the key thesis in 2-3 sentences maximum.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 200,
        temperature: 0.2,
      }),
    });

    if (!perplexityResponse.ok) {
      const errorText = await perplexityResponse.text();
      console.error('Perplexity API error:', errorText);
      return new Response(
        JSON.stringify({ success: false, error: 'Failed to generate thesis' }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    const perplexityData = await perplexityResponse.json();
    const thesis = perplexityData.choices?.[0]?.message?.content?.trim() || '';

    if (!thesis) {
      return new Response(
        JSON.stringify({ success: false, error: 'No thesis generated' }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        }
      );
    }

    const response: ThesisResponse = {
      success: true,
      thesis,
      ticker,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });

  } catch (error) {
    console.error('Thesis generation error:', error);
    return new Response(
      JSON.stringify({ success: false, error: 'Internal server error' }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}
