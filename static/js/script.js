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
                if (book.is_follow) row.classList.add('star-row'); // 设置行背景颜色

                const subIcon = data.info?.follow_books?.includes(book.url)
                    ? '<a href="#" class="sub-link followed" data-url="' + book.url + '" data-sub="true">★</a>'
                    : '<a href="#" class="sub-link unfollowed" data-url="' + book.url + '" data-sub="false">☆</a>';

                row.innerHTML = `
                            <td>${subIcon} <a href="${book.url}" target="_blank" class="text-decoration-none">${book.title}</a></td>
                            <td>${book.author}</td>
                            <td>${book.type || '未知'}</td>
                            <td>${book.word_count}</td>
                            <td>${book.last_update_date || '未知'}</td>
                            <td>${book.is_follow ? '是' : '否'}</td>
                        `;
                bookList.appendChild(row);
            });

            const followBookList = document.getElementById('follow-book-list');
            followBookList.innerHTML = ''; // 清空现有数据
            data.data?.filter(book => data.info?.follow_books?.includes(book.url)).forEach(book => {
                const row = document.createElement('tr');
                const subIcon = data.info?.follow_books?.includes(book.url)
                    ? '<a href="#" class="sub-link followed" data-url="' + book.url + '" data-sub="true">★</a>'
                    : '<a href="#" class="sub-link unfollowed" data-url="' + book.url + '" data-sub="false">☆</a>';
                row.innerHTML = `
                            <td>${subIcon} <a href="${book.url}" class="text-decoration-none">${book.title}</a></td>
                            <td>${book.author}</td>
                            <td>${book.type || '未知'}</td>
                            <td>${book.word_count}</td>
                            <td>${book.last_update_date || '未知'}</td>
                        `;
                followBookList.appendChild(row);
            });

            // 为每个关注链接添加事件监听
            document.querySelectorAll('.sub-link').forEach(link => {
                link.addEventListener('click', event => {
                    event.preventDefault();
                    const url = link.getAttribute('data-url');
                    const isSub = link.getAttribute('data-sub') === 'true';
                    fetch('api/sub', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, is_sub: !isSub })
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
const addAuthorInput = document.getElementById('add-author-input');
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

function performSearch() {
    const query = searchInput.value.toLowerCase();
    const rows = document.querySelectorAll('#book-list tr');

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