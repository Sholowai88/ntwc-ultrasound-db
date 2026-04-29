// Create a backup
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
        const { includeEquipment, includeUsers, includeAudit, includeSettings } = await context.request.json();
        
        // Get current data
        let fullData = null;
        const savedData = await context.env.DB.get('database');
        if (savedData) {
            fullData = JSON.parse(savedData);
        }
        
        if (!fullData) {
            fullData = { equipment: [], users: [], auditLogs: [], settings: {} };
        }
        
        const backupData = {
            version: '2.0',
            timestamp: new Date().toISOString(),
            backupId: Date.now().toString()
        };
        
        if (includeEquipment) backupData.equipment = fullData.equipment;
        if (includeUsers) backupData.users = fullData.users;
        if (includeAudit) backupData.auditLogs = fullData.auditLogs;
        if (includeSettings) backupData.settings = fullData.settings;
        
        // Also store backup in KV (optional)
        const backupKey = `backup_${Date.now()}`;
        await context.env.DB.put(backupKey, JSON.stringify(backupData));
        
        return new Response(JSON.stringify({
            success: true,
            backup: backupData,
            message: 'Backup created'
        }), { headers });
        
    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: error.message
        }), { status: 500, headers });
    }
}