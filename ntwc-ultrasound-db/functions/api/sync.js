// Sync data - merges changes from multiple users
export async function onRequest(context) {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    };
    
    if (context.request.method === 'OPTIONS') {
        return new Response(null, { headers });
    }
    
    try {
        const { clientData } = await context.request.json();
        
        // Get current server data
        let serverData = null;
        const savedData = await context.env.DB.get('database');
        if (savedData) {
            serverData = JSON.parse(savedData);
        }
        
        if (!serverData) {
            serverData = { equipment: [], users: [], auditLogs: [], settings: {} };
        }
        
        // Merge data - combine both sources, remove duplicates by ID
        const mergedEquipment = mergeById(serverData.equipment || [], clientData.equipment || []);
        const mergedUsers = mergeById(serverData.users || [], clientData.users || []);
        
        // For audit logs, combine and keep newest first
        const allAuditLogs = [...(serverData.auditLogs || []), ...(clientData.auditLogs || [])];
        const uniqueAudit = new Map();
        allAuditLogs.forEach(log => {
            if (log.id) uniqueAudit.set(log.id.toString(), log);
        });
        let mergedAudit = Array.from(uniqueAudit.values());
        mergedAudit.sort((a, b) => b.id - a.id);
        if (mergedAudit.length > 200) mergedAudit = mergedAudit.slice(0, 200);
        
        const mergedData = {
            equipment: mergedEquipment,
            users: mergedUsers,
            auditLogs: mergedAudit,
            settings: { ...clientData.settings, ...serverData.settings },
            lastUpdated: new Date().toISOString()
        };
        
        // Save merged data
        await context.env.DB.put('database', JSON.stringify(mergedData));
        await context.env.DB.put('last_updated', mergedData.lastUpdated);
        
        return new Response(JSON.stringify({
            success: true,
            data: mergedData,
            serverTimestamp: mergedData.lastUpdated,
            message: 'Sync completed'
        }), { headers });
        
    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: error.message
        }), { status: 500, headers });
    }
}

// Helper function to merge arrays by ID (newer version wins)
function mergeById(arr1, arr2) {
    const map = new Map();
    
    arr1.forEach(item => {
        if (item.id) map.set(item.id.toString(), item);
    });
    
    arr2.forEach(item => {
        if (item.id) map.set(item.id.toString(), item);
    });
    
    return Array.from(map.values());
}