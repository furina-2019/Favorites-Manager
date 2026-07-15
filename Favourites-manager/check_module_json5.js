const fs = require('fs');
const path = require('path');

try {
    const filePath = path.join(__dirname, 'entry', 'src', 'main', 'module.json5');
    console.log('检查文件路径:', filePath);
    
    if (!fs.existsSync(filePath)) {
        console.error('文件不存在:', filePath);
        process.exit(1);
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    console.log('文件读取成功，大小:', content.length, '字符');
    
    // 检查BOM标记
    if (content.charCodeAt(0) === 0xFEFF) {
        console.error('文件包含BOM标记（UTF-8 with BOM）');
    } else {
        console.log('文件不包含BOM标记');
    }
    
    // 检查是否有不可见字符
    const lines = content.split('\n');
    console.log('文件行数:', lines.length);
    
    // 检查每行是否有特殊字符
    for (let i = 0; i < Math.min(lines.length, 10); i++) {
        const line = lines[i];
        const hasSpecial = /[^\x00-\x7F]/.test(line);
        if (hasSpecial) {
            console.log(`第${i+1}行包含非ASCII字符:`, line.substring(0, 50));
        }
    }
    
    console.log('文件检查完成');
} catch (error) {
    console.error('检查文件时出错:', error.message);
    process.exit(1);
}