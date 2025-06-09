
// 初始化页面
function initPage() {
    try {
        loadAllLogs();
    } catch (e) {
        console.error('加载日志失败:', e);
    }
}

let currentPage = 1;
let totalRecords = 0;

// 加载日志数据(带分页)
function loadLogs(page = 1) {
    const tbody = document.querySelector('#log-table tbody');
    if (!tbody) return;
    
    // 显示加载状态
    const loadingRow = document.createElement('tr');
    loadingRow.innerHTML = '<td colspan="17" class="text-center">加载中...</td>';
    tbody.innerHTML = '';
    tbody.appendChild(loadingRow);
    
    fetch(`/api/logs?page=${page}&size=25`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                currentPage = page;
                totalRecords = data.total;
                // 清除加载状态
                tbody.innerHTML = '';
                renderLogData(data);
                updatePaginationInfo(data.total, page);
            }
        })
        .catch(error => {
            console.error('加载日志数据失败:', error);
            tbody.innerHTML = `<tr><td colspan="17" class="text-center">加载失败: ${error.message}</td></tr>`;
        });
}

// 初始化页面
function initPage() {
    try {
        loadLogs(1);
    } catch (e) {
        console.error('加载日志失败:', e);
    }
}

// 渲染日志数据
function renderLogData(response) {
    const tbody = document.querySelector('#log-table tbody');
    if (!tbody) return;

    response.data.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox" class="log-checkbox" data-id="${log.id}"></td>
            <td>${formatDate(log.date) || ''}</td>
            <td>${log.time || ''}</td>
            <td>${log.callsign || ''}</td>
            <td>${log.frequency || ''}</td>
            <td>${log.mode || ''}</td>
            <td>${log.equipment || ''}</td>
            <td>${log.antenna || ''}</td>
            <td>${log.power || ''}</td>
            <td>${log.dxcc || ''}</td>
            <td>${log.grid || ''}</td>
            <td>${log.province || ''}</td>
            <td>${log.band || ''}</td>
            <td>${getQSLStatusText(log.qslcard)}</td>
            <td>${log.notes || ''}</td>
            <td>${log.status || ''}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${log.id}">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    // 初始化复选框事件监听
    const checkboxes = document.querySelectorAll('.log-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // 如果取消单个复选框，确保全选框也取消
            const selectAll = document.getElementById('select-all');
            if (selectAll && !this.checked && selectAll.checked) {
                selectAll.checked = false;
            }
            updateButtonStates();
        });
    });

    // 更新分页信息
    updatePaginationInfo(response.total);
}

// 更新按钮状态
function updateButtonStates() {
    const selectedCount = document.querySelectorAll('.log-checkbox:checked').length;
    const editBtn = document.getElementById('edit-selected');
    const deleteBtn = document.getElementById('delete-selected');
    
    if (editBtn) editBtn.disabled = selectedCount === 0;
    if (deleteBtn) deleteBtn.disabled = selectedCount === 0;
}

// 格式化日期为年月日格式
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}年${month}月${day}日`;
}

// 获取QSL状态文本
function getQSLStatusText(status) {
    const statusMap = {
        0: '未发卡',
        1: '已发卡',
        2: 'eyeball'
    };
    return statusMap[status] || '未知';
}

// 更新分页信息
function updatePaginationInfo(total, currentPage) {
    const totalPages = Math.ceil(total / 25);
    const prevPage = document.getElementById('prev-page');
    const nextPage = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    // 更新按钮状态
    prevPage.classList.toggle('disabled', currentPage <= 1);
    nextPage.classList.toggle('disabled', currentPage >= totalPages);
    
    // 更新分页信息显示
    if (pageInfo) {
        pageInfo.textContent = `第 ${currentPage} 页，共 ${totalPages} 页 (${total} 条记录)`;
    }
    
    // 添加分页按钮事件
    prevPage.onclick = () => {
        if (currentPage > 1) loadLogs(currentPage - 1);
    };
    
    nextPage.onclick = () => {
        if (currentPage < totalPages) loadLogs(currentPage + 1);
    };
}

// 初始化全选功能
function initSelectAll() {
    const selectAll = document.getElementById('select-all');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.log-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateButtonStates(); // 全选变化时更新按钮状态
        });
    }
}

// 初始化编辑按钮
function initEditButtons() {
    // 确保使用正确的按钮选择器
    const editSelectedBtn = document.getElementById('edit-selected');
    if (editSelectedBtn) {
        editSelectedBtn.addEventListener('click', function() {
            const selectedIds = getSelectedLogIds();
            if (selectedIds.length === 0) {
                alert('请至少选择一条记录');
                return;
            }
            if (selectedIds.length > 1) {
                alert('一次只能编辑一条记录，请取消多余选择');
                return;
            }
            
            // 加载第一条选中记录的数据用于编辑
            fetch(`/api/logs/${selectedIds[0]}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const log = data.data;
                        // 填充表单数据
                        document.getElementById('edit-id').value = log.id;
                        document.getElementById('edit-callsign').value = log.callsign || '';
                        document.getElementById('edit-frequency').value = log.frequency || '';
                        document.getElementById('edit-mode').value = log.mode || 'SSB';
                        document.getElementById('edit-equipment').value = log.equipment || '';
                        document.getElementById('edit-antenna').value = log.antenna || '';
                        document.getElementById('edit-power').value = log.power || '';
                        document.getElementById('edit-dxcc').value = log.dxcc || '';
                        document.getElementById('edit-grid').value = log.grid || '';
                        document.getElementById('edit-province').value = log.province || '';
                        document.getElementById('edit-band').value = log.band || '';
                        document.getElementById('edit-qslcard').value = log.qslcard || '0';
                        document.getElementById('edit-notes').value = log.notes || '';
                        // 格式化日期为yyyy-mm-dd格式
                        const dateObj = log.date ? new Date(log.date) : new Date();
                        const formattedDate = dateObj.toISOString().split('T')[0];
                        document.getElementById('edit-date').value = formattedDate;
                        
                        // 格式化时间为HH:MM格式
                        const timeObj = log.time ? new Date(`1970-01-01T${log.time}Z`) : new Date();
                        const hours = String(timeObj.getHours()).padStart(2, '0');
                        const minutes = String(timeObj.getMinutes()).padStart(2, '0');
                        document.getElementById('edit-time').value = `${hours}:${minutes}`;
                        
                        // 尝试两种方式显示模态框
                        try {
                            // 方式1: 使用Bootstrap原生JS
                            const editModal = new bootstrap.Modal(document.getElementById('editModal'));
                            editModal.show();
                        } catch (e) {
                            console.log('Bootstrap JS方式失败，尝试jQuery方式:', e);
                            // 方式2: 使用jQuery作为备选
                            $('#editModal').modal('show');
                        }
                    }
                });
        });
    }
}

// 初始化删除按钮
function initDeleteButton() {
    const deleteBtn = document.getElementById('delete-selected');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const selectedIds = getSelectedLogIds();
            if (selectedIds.length === 0) {
                alert('请至少选择一条记录');
                return;
            }
            
            if (confirm('确定要删除选中的记录吗？此操作不可撤销！')) {
                if (confirm('再次确认：您真的要删除这些记录吗？')) {
                    // 执行删除操作
                    deleteSelectedLogs(selectedIds);
                }
            }
        });
    }
}

// 获取选中的记录ID
function getSelectedLogIds() {
    const checkboxes = document.querySelectorAll('.log-checkbox:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.dataset.id);
}

// 删除选中的记录
function deleteSelectedLogs(ids) {
    // 将ID数组转换为逗号分隔的字符串
    const idParam = ids.join(',');
    fetch(`/api/logs/del?id=${idParam}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('删除成功');
            initPage(); // 刷新列表
        } else {
            alert('删除失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('删除错误:', error);
        alert('删除过程中发生错误');
    });
}

// 确保jQuery已加载
function ensureJQueryLoaded() {
    return new Promise((resolve, reject) => {
        if (typeof jQuery !== 'undefined') {
            resolve();
        } else {
            const script = document.createElement('script');
            script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
            script.onload = () => resolve();
            script.onerror = () => {
                reject(new Error('Failed to load jQuery'));
            };
            document.head.appendChild(script);
        }
    });
}

// 页面加载初始化
document.addEventListener('DOMContentLoaded', function() {
    ensureJQueryLoaded()
        .then(() => {
            try {
                initPage();
                initSelectAll();
                initEditButtons();
                initDeleteButton();
                updateButtonStates();
            } catch (e) {
                console.error('初始化页面失败:', e);
            }
        })
        .catch(error => {
            alert('系统初始化失败，请刷新页面重试');
        });
    
    // 初始化模态框保存按钮
    document.getElementById('save-changes')?.addEventListener('click', function() {
        const selectedIds = getSelectedLogIds();
        // 准备表单数据并进行基本处理
        const formData = {
            callsign: document.getElementById('edit-callsign').value.trim(),
            frequency: parseFloat(document.getElementById('edit-frequency').value) || 0,
            mode: document.getElementById('edit-mode').value.trim(),
            equipment: document.getElementById('edit-equipment').value.trim(),
            antenna: document.getElementById('edit-antenna').value.trim(),
            power: parseFloat(document.getElementById('edit-power').value) || 0,
            dxcc: document.getElementById('edit-dxcc').value.trim(),
            grid: document.getElementById('edit-grid').value.trim(),
            province: document.getElementById('edit-province').value.trim(),
            band: document.getElementById('edit-band').value.trim(),
            qslcard: parseInt(document.getElementById('edit-qslcard').value) || 0,
            notes: document.getElementById('edit-notes').value.trim(),
            date: document.getElementById('edit-date').value.trim(),
            time: document.getElementById('edit-time').value.trim()
        };

        // 验证必填字段
        if (!formData.callsign || !formData.mode || isNaN(formData.frequency)) {
            alert('呼号、频率和模式是必填字段，且频率必须是数字');
            return;
        }

        // 批量更新选中的记录
        Promise.all(selectedIds.map(id => {
            return fetch(`/api/logs/${id}`, {
                method: 'PUT',
                body: JSON.stringify(formData),
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            })
            .then(async response => {
                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.message || `记录 ${id} 更新失败`);
                }
                return data;
            });
        }))
        .then(() => {
            alert('更新成功');
            try {
                // 尝试两种方式关闭模态框
                try {
                    bootstrap.Modal.getInstance(document.getElementById('editModal'))?.hide();
                } catch (e) {
                    $('#editModal').modal('hide');
                }
            } catch (e) {
                console.error('关闭模态框失败:', e);
            }
            loadLogs(currentPage); // 刷新当前页列表
        })
        .catch(error => {
            console.error('更新错误:', error);
            alert(`更新失败: ${error.message}`);
        });
    }); // 闭合ensureJQueryLoaded().then()
}); // 闭合DOMContentLoaded事件处理函数
