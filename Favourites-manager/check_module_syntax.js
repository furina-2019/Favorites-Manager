const fs = require('fs');
const path = require('path');

function validateModuleJson5(filePath) {
    try {
        console.log('检查文件:', filePath);
        const content = fs.readFileSync(filePath, 'utf8');
        
        // 检查文件编码
        if (content.charCodeAt(0) === 0xFEFF) {
            console.error('警告: 文件包含UTF-8 BOM标记');
        }
        
        // 检查基本语法
        const lines = content.split('\n');
        let lineNumber = 1;
        let inString = false;
        let escapeNext = false;
        
        for (const line of lines) {
            // 检查每行的括号平衡
            let braceCount = 0;
            let bracketCount = 0;
            let quoteCount = 0;
            
            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                
                if (escapeNext) {
                    escapeNext = false;
                    continue;
                }
                
                if (char === '\\') {
                    escapeNext = true;
                    continue;
                }
                
                if (char === '"') {
                    quoteCount++;
                    inString = !inString;
                } else if (!inString) {
                    if (char === '{') braceCount++;
                    if (char === '}') braceCount--;
                    if (char === '[') bracketCount++;
                    if (char === ']') bracketCount--;
                }
            }
            
            // 检查引号是否成对
            if (quoteCount % 2 !== 0) {
                console.error(`第${lineNumber}行: 引号不成对`);
            }
            
            // 检查括号平衡
            if (braceCount !== 0) {
                console.error(`第${lineNumber}行: 大括号不平衡 (${braceCount > 0 ? '缺少}' : '多余}')`);
            }
            
            if (bracketCount !== 0) {
                console.error(`第${lineNumber}行: 方括号不平衡 (${bracketCount > 0 ? '缺少]' : '多余]'})`);
            }
            
            lineNumber++;
        }
        
        // 检查关键字段
        const requiredSections = [
            '"module": {',
            '"name":',
            '"type":',
            '"abilities": [',
            '"requestPermissions": ['
        ];
        
        console.log('\n检查关键字段:');
        for (const section of requiredSections) {
            if (content.includes(section)) {
                console.log(`✓ 找到: ${section}`);
            } else {
                console.error(`✗ 缺少: ${section}`);
            }
        }
        
        // 检查权限配置
        console.log('\n检查权限配置:');
        const permissionStart = content.indexOf('"requestPermissions": [');
        if (permissionStart !== -1) {
            const permissionEnd = content.indexOf(']', permissionStart);
            const permissionSection = content.substring(permissionStart, permissionEnd + 1);
            
            // 检查每个权限块
            const permissionBlocks = permissionSection.match(/\{[^{}]*\}/g);
            if (permissionBlocks) {
                console.log(`找到 ${permissionBlocks.length} 个权限配置`);
                
                permissionBlocks.forEach((block, index) => {
                    console.log(`\n权限 ${index + 1}:`);
                    
                    // 检查name字段
                    if (block.includes('"name":')) {
                        const nameMatch = block.match(/"name":\s*"([^"]+)"/);
                        if (nameMatch) {
                            console.log(`  name: ${nameMatch[1]}`);
                            
                            // 检查是否是user_grant权限
                            const userGrantPermissions = [
                                'ohos.permission.INTERNET',
                                'ohos.permission.GET_NETWORK_INFO',
                                'ohos.permission.START_ABILITIES_NORMAL'
                            ];
                            
                            if (userGrantPermissions.includes(nameMatch[1])) {
                                console.log(`  ⚠️  这是user_grant权限，需要reason和usedScene`);
                                
                                if (!block.includes('"reason":')) {
                                    console.error(`  ✗ 缺少reason字段`);
                                } else {
                                    console.log(`  ✓ 有reason字段`);
                                }
                                
                                if (!block.includes('"usedScene":')) {
                                    console.error(`  ✗ 缺少usedScene字段`);
                                } else {
                                    console.log(`  ✓ 有usedScene字段`);
                                }
                            }
                        }
                    }
                });
            }
        }
        
        console.log('\n文件语法检查完成');
        
    } catch (error) {
        console.error('检查文件时出错:', error.message);
    }
}

// 运行检查
validateModuleJson5('entry/src/main/module.json5');