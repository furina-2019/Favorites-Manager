const fs = require('fs');
const JSON5 = require('json5');

try {
    const content = fs.readFileSync('entry/src/main/module.json5', 'utf8');
    console.log('读取文件成功，文件大小:', content.length, '字符');
    
    // 尝试解析JSON5
    const parsed = JSON5.parse(content);
    console.log('JSON5解析成功');
    
    // 检查权限配置
    if (parsed.module && parsed.module.requestPermissions) {
        console.log('权限配置检查:');
        parsed.module.requestPermissions.forEach((perm, index) => {
            console.log(`权限 ${index + 1}: ${perm.name}`);
            console.log(`  reason: ${perm.reason || '未设置'}`);
            console.log(`  usedScene: ${perm.usedScene ? '已设置' : '未设置'}`);
        });
    }
    
    // 检查其他关键字段
    console.log('\n关键字段检查:');
    console.log('module.name:', parsed.module?.name);
    console.log('module.type:', parsed.module?.type);
    console.log('module.mainElement:', parsed.module?.mainElement);
    console.log('abilities数量:', parsed.module?.abilities?.length || 0);
    console.log('extensionAbilities数量:', parsed.module?.extensionAbilities?.length || 0);
    
} catch (error) {
    console.error('解析错误:', error.message);
    console.error('错误位置:', error.lineNumber, '行, 列', error.columnNumber);
    
    // 尝试找到具体错误位置
    if (error.message.includes('JSON5')) {
        const lines = content.split('\n');
        const lineNum = error.lineNumber || 0;
        const colNum = error.columnNumber || 0;
        
        if (lineNum > 0 && lineNum <= lines.length) {
            console.log('\n错误位置附近的代码:');
            const start = Math.max(0, lineNum - 3);
            const end = Math.min(lines.length, lineNum + 2);
            for (let i = start; i < end; i++) {
                console.log(`${i + 1}: ${lines[i]}`);
            }
        }
    }
}