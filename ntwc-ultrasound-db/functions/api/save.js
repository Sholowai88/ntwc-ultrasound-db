// Save data to Cloudflare KV storage
export async function onRequest(context) {
    // Allow requests from anywhere (CORS)
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    };
    
    // Handle preflight request
    if (context.request.method === 'OPTIONS') {
        return new Response(null, { headers });
    }
    
    try {
        const { equipment, users, auditLogs, settings } = await context.request.json();
        
        const data = {
            equipment: equipment || [],
            users: users || [],
            auditLogs: auditLogs || [],
            settings: settings || { autoSave: true },
            lastUpdated: new Date().toISOString(),
            version: '2.0'
        };
        
        // Store in Cloudflare KV
        await context.env.DB.put('database', JSON.stringify(data));
        await context.env.DB.put('last_updated', data.lastUpdated);
        
        return new Response(JSON.stringify({
            success: true,
            message: 'Data saved successfully',
            timestamp: data.lastUpdated
        }), { headers });
        
    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: error.message
        }), { status: 500, headers });
    }
}