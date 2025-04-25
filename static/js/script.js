const apiUrl = 'api/data'; // 请替换为实际的 API 地址

function loadData(apiEndpoint) {
    fetch(apiEndpoint)
        .then(response => response.json())
        .then(data => {
            // 更新书籍列表
            const bookList = document.getElementById('book-list');
            bookList.innerHTML = ''; // 清空现有数据

            // 更新日期显示
            const updateDateElement = document.getElementById('update-date');
            updateDateElement.textContent = `数据更新于：${data.info?.last_fetch_data_date}`;

            // 更新历史通知
            const notificationList = document.getElementById('notification-list');
            notificationList.innerHTML = ''; // 清空现有通知记录
            data.notification_history?.forEach(notification => {
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                listItem.textContent = notification;
                notificationList.appendChild(listItem);
            });

            // 显示关注的作者
            const authorsList = document.getElementById('authors-list');
            authorsList.innerHTML = ''; // 清空现有作者列表
            data.info?.follow_authors?.forEach(author => {
                const authorElement = document.createElement('div');
                authorElement.className = 'd-flex align-items-center me-3 mb-2';
                authorElement.innerHTML = `
                            <span class="badge bg-secondary me-2">
                                ${author}
                                <a href="#" data-author="${author}" class="btn-remove-author text-decoration-none" style="color: white;">×</a>
                            </span>
                        `;
                authorsList.appendChild(authorElement);
            });

            // 为每个删除按钮添加事件监听
            document.querySelectorAll('.btn-remove-author').forEach(button => {
                button.addEventListener('click', event => {
                    const author = button.getAttribute('data-author');
                    fetch(`api/author?author=${author}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' }
                    })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('删除失败');
                            }
                            loadData(apiUrl); // 重新加载数据
                        })
                        .catch(error => {
                            alert(`删除失败: ${error.message}`);
                        });
                });
            });

            // 插入书籍数据
            data.data?.forEach(book => {
                const row = document.createElement('tr');
                if (book.is_follow || data.info?.follow_books?.some(fb => fb.url === book.url)) row.classList.add('star-row'); // 设置行背景颜色

                const followIcon = data.info?.follow_books?.some(fb => fb.url === book.url)
                    ? '<a href="#" class="follow-link followed" data-url="' + book.url + '" data-follow="true">★</a>'
                    : '<a href="#" class="follow-link unfollowed" data-url="' + book.url + '" data-follow="false">☆</a>';

                row.innerHTML = `
                            <td>${followIcon} <a href="${book.url}" target="_blank" class="text-decoration-none">${book.title}</a></td>
                            <td>${book.author}</td>
                            <td>${book.type || '未知'}</td>
                            <td>${book.word_count}</td>
                            <td>${book.last_update_date || '未知'}</td>
                            <td>${book.is_follow || data.info?.follow_books?.some(fb => fb.url === book.url) ? '是' : '否'}</td>
                            <td>${book.is_new ? '是' : '否'}</td>
                        `;
                bookList.appendChild(row);
            });

            // 插入新书上榜数据
            const newBookList = document.getElementById('new-book-list');
            newBookList.innerHTML = ''; // 清空现有数据
            data.data?.filter(book => book.is_new).forEach(book => {
                const row = document.createElement('tr');
                const followIcon = data.info?.follow_books?.some(fb => fb.url === book.url)
                    ? '<a href="#" class="follow-link followed" data-url="' + book.url + '" data-follow="true">★</a>'
                    : '<a href="#" class="follow-link unfollowed" data-url="' + book.url + '" data-follow="false">☆</a>';

                row.innerHTML = `
                            <td>${followIcon} <a href="${book.url}" target="_blank" class="text-decoration-none">${book.title}</a></td>
                            <td>${book.author}</td>
                            <td>${book.type || '未知'}</td>
                            <td>${book.word_count}</td>
                            <td>${book.last_update_date || '未知'}</td>
                        `;
                newBookList.appendChild(row);
            });

            // 插入关注的书籍数据
            const followBookList = document.getElementById('follow-book-list');
            followBookList.innerHTML = ''; // 清空现有数据
            data.data?.filter(book => data.info?.follow_books?.some(fb => fb.url === book.url)).forEach(book => {
                const row = document.createElement('tr');
                const followIcon = data.info?.follow_books?.some(fb => fb.url === book.url)
                    ? '<a href="#" class="follow-link followed" data-url="' + book.url + '" data-follow="true">★</a>'
                    : '<a href="#" class="follow-link unfollowed" data-url="' + book.url + '" data-follow="false">☆</a>';
                const isImportant = data.info?.follow_books?.find(fb => fb.url === book.url)?.is_important || false;
                // 为重点关注的书籍添加特殊背景色
                if (isImportant) {
                    row.classList.add('table-info');
                }
                row.innerHTML = `
                            <td>
                                <input type="checkbox" class="important-checkbox" data-url="${book.url}" ${isImportant ? 'checked' : ''}>
                                ${followIcon}
                            </td>
                            <td>
                                <a href="${book.url}" class="text-decoration-none">${book.title}</a>
                            </td>
                            <td>${book.author}</td>
                            <td>${book.type || '未知'}</td>
                            <td>${book.word_count}</td>
                            <td>${book.last_update_date || '未知'}</td>
                            <td>
                                <div class="btn-group btn-group-sm" role="group">
                                    <input type="radio" class="btn-check status-radio" name="status_${book.url}" id="new_${book.url}" value="new" ${data.info?.follow_books?.find(fb => fb.url === book.url)?.status === 'new' ? 'checked' : ''}>
                                    <label class="btn btn-outline-primary py-0 px-1" for="new_${book.url}">未开始</label>
                                    
                                    <input type="radio" class="btn-check status-radio" name="status_${book.url}" id="wip_${book.url}" value="wip" ${data.info?.follow_books?.find(fb => fb.url === book.url)?.status === 'wip' ? 'checked' : ''}>
                                    <label class="btn btn-outline-primary py-0 px-1 mx-1" for="wip_${book.url}">进行中</label>
                                    
                                    <input type="radio" class="btn-check status-radio" name="status_${book.url}" id="done_${book.url}" value="done" ${data.info?.follow_books?.find(fb => fb.url === book.url)?.status === 'done' ? 'checked' : ''}>
                                    <label class="btn btn-outline-primary py-0 px-1" for="done_${book.url}">已完成</label>
                                </div>
                            </td>
                        `;
                followBookList.appendChild(row);

                // 为复选框添加事件监听
                const checkbox = row.querySelector('.important-checkbox');
                checkbox.addEventListener('change', (event) => {
                    const url = event.target.getAttribute('data-url');
                    const isImportant = event.target.checked;
                    fetch('api/important_book', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, is_important: isImportant })
                    })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('操作失败');
                            }
                            return response.json();
                        })
                        .then(() => {
                            loadData(apiUrl); // 重新加载数据
                        })
                        .catch(error => {
                            alert(`操作失败: ${error.message}`);
                            event.target.checked = !isImportant; // 恢复原状态
                        });
                });

                // 为单选框添加事件监听
                const statusRadios = row.querySelectorAll('.status-radio');
                statusRadios.forEach(radio => {
                    radio.addEventListener('change', (event) => {
                        const url = event.target.name.replace('status_', '');
                        const status = event.target.value;
                        fetch('api/book_status', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url, status })
                        })
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error('操作失败');
                                }
                                return response.json();
                            })
                            .catch(error => {
                                alert(`操作失败: ${error.message}`);
                            });
                    });
                });
            });

            // 为每个关注链接添加事件监听
            document.querySelectorAll('.follow-link').forEach(link => {
                link.addEventListener('click', event => {
                    event.preventDefault();
                    const url = link.getAttribute('data-url');
                    const isFollow = link.getAttribute('data-follow') === 'true';
                    fetch('api/follow_book', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, is_follow: !isFollow })
                    })
                        .then(response => {
                            return response.json();
                        })
                        .then(() => {
                            loadData(apiUrl); // 重新加载数据
                        })
                        .catch(error => {
                            alert(`操作失败: ${error.message}`);
                        });
                });
            });

            // 排序功能
            document.querySelectorAll('.sortable').forEach(header => {
                header.addEventListener('click', () => {
                    const column = header.getAttribute('data-column');
                    const order = header.getAttribute('data-order');
                    const bookList = document.getElementById('book-list');
                    const rows = Array.from(bookList.querySelectorAll('tr'));

                    rows.sort((a, b) => {
                        const cellA = a.querySelector(`td:nth-child(${header.cellIndex + 1})`).innerText;
                        const cellB = b.querySelector(`td:nth-child(${header.cellIndex + 1})`).innerText;

                        if (column === 'word_count') {
                            return (order === 'asc' ? 1 : -1) * (parseInt(cellA) - parseInt(cellB));
                        } else if (column === 'is_follow') {
                            return (order === 'asc' ? 1 : -1) * (cellA === '是' ? 1 : -1);
                        } else {
                            return (order === 'asc' ? 1 : -1) * cellA.localeCompare(cellB, 'zh');
                        }
                    });

                    rows.forEach(row => bookList.appendChild(row));
                    header.setAttribute('data-order', order === 'asc' ? 'desc' : 'asc');
                });
            });
        })
        .catch(error => {
            const bookList = document.getElementById('book-list');
            bookList.innerHTML = `<tr><td colspan="6" class="text-danger text-center">加载数据失败: ${error.message}</td></tr>`;
        });


}

// 初始加载数据
if (apiUrl) {
    loadData(apiUrl);
}

// 添加作者功能
const confirmAddAuthor = document.getElementById('confirm-add-author');
const newAuthorName = document.getElementById('new-author-name');

confirmAddAuthor.addEventListener('click', () => {
    const author = newAuthorName.value.trim();
    if (author) {
        fetch('api/author', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ author })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('添加失败');
                }
                loadData(apiUrl); // 重新加载数据
                newAuthorName.value = ''; // 清空输入框
                alert('添加成功');
            })
            .catch(error => {
                alert(`添加失败: ${error.message}`);
            });
    }
});

// 添加关注书功能
const confirmAddBook = document.getElementById('confirm-add-book');
const newBookId = document.getElementById('new-book-id');

confirmAddBook.addEventListener('click', () => {
    const bookId = newBookId.value.trim();
    if (bookId) {
        fetch('api/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ book_id: bookId })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('添加失败');
                }
                loadData(apiUrl); // 重新加载数据
                newBookId.value = ''; // 清空输入框
                alert('添加成功');
            })
            .catch(error => {
                alert(`添加失败: ${error.message}`);
            });
    }
});

// 获取最新数据
const getLatestData = document.getElementById('load-data-btn');
getLatestData.addEventListener('click', () => {
    fetch('api/load')
        .then(response => {
            if (!response.ok) {
                throw new Error('获取失败');
            }
            loadData(apiUrl); // 重新加载数据
            alert('获取成功');
        })
        .catch(error => {
            alert(`获取失败: ${error.message}`);
        });
    loadData(apiUrl);
});

// 搜索功能
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const sourceSearchLink = document.getElementById('search-origin');

function performSearch() {
    const query = searchInput.value.toLowerCase();
    const rows = document.querySelectorAll('#book-list tr');

    // 根据搜索内容显示或隐藏源网站搜索链接
    if (query.trim() === '') {
        sourceSearchLink.style.display = 'none';
    } else {
        sourceSearchLink.style.display = 'inline';
        sourceSearchLink.href = 'https://book.qq.com/so/' + query;
    }

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let match = false;

        // 遍历前四列（书名、作者、类型、字数）
        for (let i = 0; i < 4; i++) {
            const text = cells[i].textContent.toLowerCase();
            if (text.includes(query)) {
                match = true;
                break;
            }
        }

        row.style.display = match ? '' : 'none';
    });
}

// 绑定事件
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('input', performSearch); // 输入时实时搜索
// 添加输入事件监听器，实时更新链接显示状态
searchInput.addEventListener('input', performSearch);