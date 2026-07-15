const fs = require('fs');

try {
    const content = fs.readFileSync('entry/src/main/module.json5', 'utf8');
    console.log('文件大小:', content.length, '字符');
    
    // 检查基本结构
    if (!content.trim().startsWith('{')) {
        console.error('错误: 文件应该以 { 开头');
    }
    
    if (!content.trim().endsWith('}')) {
        console.error('错误: 文件应该以 } 结尾');
    }
    
    // 检查关键字段
    const requiredFields = ['module', 'name', 'type', 'mainElement', 'deviceTypes', 'abilities'];
    const missingFields = [];
    
    for (const field of requiredFields) {
        if (!content.includes(`"${field}"`)) {
            missingFields.push(field);
        }
    }
    
    if (missingFields.length > 0) {
        console.error('缺少必要字段:', missingFields);
    } else {
        console.log('基本字段检查通过');
    }
    
    // 检查JSON结构
    try {
        // 简单替换JSON5特性以进行基本验证
        let jsonContent = content
            .replace(/\/\/.*$/gm, '') // 移除注释
            .replace(/,\s*}/g, '}')   // 移除尾随逗号
            .replace(/,\s*]/g, ']');  // 移除尾随逗号
        
        JSON.parse(jsonContent);
        console.log('JSON语法检查通过');
    } catch (jsonError) {
        console.error('JSON语法错误:', jsonError.message);
        
        // 尝试找到错误位置
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
            // 检查常见的语法错误
            const line = lines[i];
            if (line.includes('"') && !line.includes('":')) {
                // 检查是否有未闭合的引号
                const quoteCount = (line.match(/"/g) || []).length;
                if (quoteCount % 2 !== 0) {
                    console.error(`第${i+1}行可能有未闭合的引号:`, line);
                }
            }
            
            // 检查是否有缺失的逗号
            if (i > 0 && i < lines.length - 1) {
                const prevLine = lines[i-1].trim();
                const currLine = lines[i].trim();
                if (prevLine.endsWith('}') && currLine.startsWith('{')) {
                    console.error(`第${i}行和第${i+1}行之间可能缺少逗号`);
                }
            }
        }
    }
    
    // 检查权限配置
    const permissionRegex = /"requestPermissions"\s*:\s*\[([\s\S]*?)\]/;
    const match = content.match(permissionRegex);
    if (match) {
        console.log('找到权限配置');
        const permissionSection = match[1];
        
        // 检查每个权限
        const permissionBlocks = permissionSection.match(/\{[^}]*\}/g);
        if (permissionBlocks) {
            console.log(`找到 ${permissionBlocks.length} 个权限配置`);
            
            permissionBlocks.forEach((block, index) => {
                console.log(`\n权限 ${index + 1}:`);
                
                // 检查name字段
                const nameMatch = block.match(/"name"\s*:\s*"([^"]+)"/);
                if (nameMatch) {
                    console.log(`  name: ${nameMatch[1]}`);
                    
                    // 检查reason字段
                    const reasonMatch = block.match(/"reason"\s*:\s*"([^"]+)"/);
                    if (reasonMatch) {
                        console.log(`  reason: ${reasonMatch[1]}`);
                    } else {
                        console.log(`  reason: 未找到`);
                    }
                    
                    // 检查usedScene字段
                    const usedSceneMatch = block.match(/"usedScene"\s*:\s*\{/);
                    if (usedSceneMatch) {
                        console.log(`  usedScene: 已配置`);
                    } else {
                        console.log(`  usedScene: 未找到`);
                    }
                }
            });
        }
    }
    
} catch (error) {
    console.error('验证错误:', error.message);
}