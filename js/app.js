/**
 * Investment Dashboard - Main Application Logic
 */

$(document).ready(function() {
    // Load stock data
    loadStockData();
});

function loadStockData() {
    $.ajax({
        url: 'data/stocks.json',
        dataType: 'json',
        success: function(data) {
            console.log('Loaded data:', data);
            updateMetadata(data);
            initializeTable(data.stocks);
        },
        error: function(xhr, status, error) {
            console.error('Error loading data:', error);
            showError('Failed to load stock data. Please check if the data file exists.');
        }
    });
}

function updateMetadata(data) {
    // Update last updated timestamp
    const lastUpdated = new Date(data.last_updated);
    $('#last-updated').html(`<i class="fas fa-clock"></i> Last Updated: ${lastUpdated.toLocaleString()}`);

    // Update summary stats
    $('#total-stocks').text(data.total_stocks);

    const dataromaCount = data.stocks.filter(s => s.sources.includes('Dataroma')).length;
    const substackCount = data.stocks.filter(s => s.sources.includes('Substack')).length;
    const bothCount = data.stocks.filter(s => s.sources.includes('Dataroma') && s.sources.includes('Substack')).length;

    $('#dataroma-count').text(dataromaCount);
    $('#substack-count').text(substackCount);
    $('#both-sources').text(bothCount);
}

function initializeTable(stocks) {
    const table = $('#stocksTable').DataTable({
        data: stocks,
        columns: [
            {
                data: 'ticker',
                render: function(data, type, row) {
                    return `<span class="ticker-cell">${data}</span>`;
                }
            },
            {
                data: 'company_name',
                render: function(data, type, row) {
                    return data.length > 30 ? data.substring(0, 30) + '...' : data;
                }
            },
            {
                data: 'pe_ratio',
                render: function(data, type, row) {
                    if (data === 'N/A' || data === null) return 'N/A';
                    const pe = parseFloat(data);
                    let className = '';
                    if (pe < 15) className = 'pe-low';
                    else if (pe < 25) className = 'pe-medium';
                    else className = 'pe-high';
                    return `<span class="${className}">${pe.toFixed(2)}</span>`;
                }
            },
            {
                data: 'pb_ratio',
                render: function(data, type, row) {
                    return formatNumber(data);
                }
            },
            {
                data: 'week_52_high',
                render: function(data, type, row) {
                    return formatCurrency(data);
                }
            },
            {
                data: 'week_52_low',
                render: function(data, type, row) {
                    return formatCurrency(data);
                }
            },
            {
                data: 'peg_ratio',
                render: function(data, type, row) {
                    return formatNumber(data);
                }
            },
            {
                data: 'insider_pct',
                render: function(data, type, row) {
                    return formatPercentage(data);
                }
            },
            {
                data: 'sources',
                render: function(data, type, row) {
                    let badges = '';
                    if (data.includes('Dataroma')) {
                        badges += '<span class="badge bg-success source-badge">Dataroma</span>';
                    }
                    if (data.includes('Substack')) {
                        badges += '<span class="badge bg-info source-badge">Substack</span>';
                    }
                    return badges;
                }
            },
            {
                data: 'dataroma_data.investors',
                render: function(data, type, row) {
                    if (!data || data.length === 0) return '-';
                    if (data.length === 1) return data[0];
                    return `<span class="investor-list" title="${data.join(', ')}">${data.length} investors</span>`;
                },
                defaultContent: '-'
            },
            {
                data: 'dataroma_data.activity',
                render: function(data, type, row) {
                    if (!data || data === 'Hold') return '-';

                    let badgeClass = 'bg-secondary';
                    if (data.includes('New')) badgeClass = 'activity-new';
                    else if (data.includes('Increased')) badgeClass = 'activity-increase';
                    else if (data.includes('Decreased')) badgeClass = 'activity-decrease';

                    return `<span class="badge ${badgeClass}">${data}</span>`;
                },
                defaultContent: '-'
            },
            {
                data: 'substack_data.thesis',
                render: function(data, type, row) {
                    if (!data) return '-';
                    const short = data.length > 50 ? data.substring(0, 50) + '...' : data;
                    return `<span class="thesis-cell" title="${escapeHtml(data)}">${escapeHtml(short)}</span>`;
                },
                defaultContent: '-'
            },
            {
                data: 'stockanalysis_link',
                render: function(data, type, row) {
                    return `<a href="${data}" target="_blank" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-external-link-alt"></i>
                    </a>`;
                }
            }
        ],
        pageLength: 50,
        lengthMenu: [[25, 50, 100, -1], [25, 50, 100, "All"]],
        order: [[2, 'asc']], // Sort by PE ratio
        responsive: true,
        dom: '<"row"<"col-sm-12 col-md-6"B><"col-sm-12 col-md-6"f>>rt<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        buttons: [
            {
                extend: 'csv',
                text: '<i class="fas fa-file-csv"></i> Export CSV',
                className: 'btn btn-success btn-sm'
            },
            {
                extend: 'excel',
                text: '<i class="fas fa-file-excel"></i> Export Excel',
                className: 'btn btn-success btn-sm'
            },
            {
                extend: 'copy',
                text: '<i class="fas fa-copy"></i> Copy',
                className: 'btn btn-secondary btn-sm'
            }
        ],
        language: {
            search: "Search stocks:",
            lengthMenu: "Show _MENU_ stocks per page",
            info: "Showing _START_ to _END_ of _TOTAL_ stocks",
            infoEmpty: "No stocks available",
            infoFiltered: "(filtered from _MAX_ total stocks)",
            zeroRecords: "No matching stocks found"
        }
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
}

function formatNumber(value) {
    if (value === 'N/A' || value === null || value === undefined) return 'N/A';
    const num = parseFloat(value);
    if (isNaN(num)) return 'N/A';
    return num.toFixed(2);
}

function formatCurrency(value) {
    if (value === 'N/A' || value === null || value === undefined) return 'N/A';
    const num = parseFloat(value);
    if (isNaN(num)) return 'N/A';
    return '$' + num.toFixed(2);
}

function formatPercentage(value) {
    if (value === 'N/A' || value === null || value === undefined) return 'N/A';
    const num = parseFloat(value);
    if (isNaN(num)) return 'N/A';
    return num.toFixed(2) + '%';
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function showError(message) {
    const errorHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <strong>Error!</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(errorHtml);
}
