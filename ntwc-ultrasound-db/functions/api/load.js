// Load data from Cloudflare KV storage
export async function onRequest(context) {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    };
    
    if (context.request.method === 'OPTIONS') {
        return new Response(null, { headers });
    }
    
    try {
        let data = null;
        
        // Retrieve from KV storage
        const savedData = await context.env.DB.get('database');
        if (savedData) {
            data = JSON.parse(savedData);
        }
        
        // Return default structure if no data exists
        if (!data) {
            data = {
                equipment: [],
                users: [],
                auditLogs: [],
                settings: { autoSave: true },
                lastUpdated: null,
                version: '2.0'
            };
        }
        
        return new Response(JSON.stringify({
            success: true,
            data: data,
            timestamp: new Date().toISOString()
        }), { headers });
        
    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: error.message
        }), { status: 500, headers });
    }
}