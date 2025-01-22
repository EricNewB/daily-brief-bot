// 获取DOM元素
const timeWindow = document.getElementById('timeWindow');
const timeValue = document.getElementById('timeValue');
const saveBtn = document.getElementById('saveBtn');
const runBtn = document.getElementById('runBtn');
const statusContent = document.getElementById('statusContent');

// 更新时间窗口显示
timeWindow.addEventListener('input', (e) => {
    timeValue.textContent = `${e.target.value}天`;
});

// 保存配置
saveBtn.addEventListener('click', async () => {
    const config = {
        time_filter: {
            max_age_days: parseInt(timeWindow.value)
        },
        categories: {},
        sources: {}
    };

    // 获取类别设置
    document.querySelectorAll('input[name="category"]').forEach(input => {
        config.categories[input.value] = input.checked;
    });

    // 获取来源设置
    document.querySelectorAll('input[name="source"]').forEach(input => {
        config.sources[input.value] = input.checked;
    });

    try {
        const response = await fetch('/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            statusContent.textContent = '配置已保存';
            setTimeout(() => {
                statusContent.textContent = '等待操作...';
            }, 2000);
        } else {
            throw new Error('保存失败');
        }
    } catch (error) {
        statusContent.textContent = '保存配置失败: ' + error.message;
    }
});

// 运行爬虫
runBtn.addEventListener('click', async () => {
    statusContent.textContent = '正在运行爬虫...';
    
    try {
        const response = await fetch('/run_crawler', {
            method: 'POST'
        });

        const data = await response.json();
        statusContent.textContent = `爬取完成！获取到 ${data.count} 条内容`;
    } catch (error) {
        statusContent.textContent = '运行失败: ' + error.message;
    }
});