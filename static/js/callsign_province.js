
/**
 * 根据呼号自动填充省份
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('callsign_province.js loaded - 脚本已加载');
    console.log('正在查找表单元素...');
    const callsignInput = document.getElementById('callsign-field');
    const provinceInput = document.getElementById('province-field');
    
    console.log('找到的表单元素:', {
        callsignInput: callsignInput ? '找到' : '未找到',
        provinceInput: provinceInput ? '找到' : '未找到'
    });
    console.log('页面所有元素:', document.querySelectorAll('*'));
    
    if (callsignInput && provinceInput) {
        callsignInput.addEventListener('input', function() {
            console.log('Callsign input changed:', this.value);
            const callsign = this.value.toUpperCase();
            
            // 只处理B开头的呼号
            if (!callsign.startsWith('B')) {
                console.log('非B开头呼号，已清空省份字段');
                return;
            }
            
            // 确保呼号长度足够
            if (callsign.length < 4) {
                console.log('呼号长度不足，无法判断');
                return;
            }
            
            const regionDigit = callsign.charAt(2); // 第三位数字
            const provinceLetter = callsign.charAt(3); // 第四位字母
            console.log('Processing digit:', regionDigit, 'letter:', provinceLetter);
                
                // 省份映射表 (根据第三位数字和第四位字母)
                const provinceMap = {
                    '1': { // 北京
                        'A-X': '北京'
                    },
                    '2': { // 黑龙江、吉林、辽宁
                        'A-H': '黑龙江',
                        'I-P': '吉林',
                        'Q-X': '辽宁'
                    },
                    '3': { // 天津、内蒙古、河北、山西
                        'A-F': '天津',
                        'G-L': '内蒙古',
                        'M-R': '河北',
                        'S-X': '山西'
                    },
                    '4': { // 上海、山东、江苏
                        'A-H': '上海',
                        'I-P': '山东',
                        'Q-X': '江苏'
                    },
                    '5': { // 浙江、江西、福建
                        'A-H': '浙江',
                        'I-P': '江西',
                        'Q-X': '福建'
                    },
                    '6': { // 安徽、河南、湖北
                        'A-H': '安徽',
                        'I-P': '河南',
                        'Q-X': '湖北'
                    },
                    '7': { // 湖南、广东、广西、海南
                        'A-H': '湖南',
                        'I-P': '广东',
                        'Q-X': '广西',
                        'Y-Z': '海南'
                    },
                    '8': { // 四川、重庆、贵州、云南
                        'A-F': '四川',
                        'G-L': '重庆',
                        'M-R': '贵州',
                        'S-X': '云南'
                    },
                    '9': { // 陕西、甘肃、宁夏、青海
                        'A-F': '陕西',
                        'G-L': '甘肃',
                        'M-R': '宁夏',
                        'S-X': '青海'
                    },
                    '0': { // 新疆、西藏
                        'A-F': '新疆',
                        'G-L': '西藏'
                    }
                };

                let province = '';
                if (provinceMap[regionDigit]) {
                    for (const [range, prov] of Object.entries(provinceMap[regionDigit])) {
                        const [start, end] = range.split('-');
                        if (provinceLetter >= start && provinceLetter <= end) {
                            province = prov;
                            break;
                        }
                    }
                }
                
                provinceInput.value = province;
                console.log('Set province to:', province || '空');
        });
    } else {
        console.error('错误：未找到必需的表单元素！');
        console.error('当前页面HTML结构:', document.documentElement.innerHTML);
    }
});
