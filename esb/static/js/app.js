/* ESB custom JavaScript */

document.addEventListener('DOMContentLoaded', function () {
  // --- Clickable queue rows (with keyboard support) ---
  document.querySelectorAll('.queue-row[data-href]').forEach(function (row) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function () {
      window.location.href = row.dataset.href;
    });
    row.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        window.location.href = row.dataset.href;
      }
    });
  });

  // --- Kanban card keyboard navigation (Space key; Enter is native on <a>) ---
  document.querySelectorAll('a.kanban-card').forEach(function (card) {
    card.addEventListener('keydown', function (e) {
      if (e.key === ' ') {
        e.preventDefault();
        window.location.href = card.href;
      }
    });
  });

  // --- Queue table sorting ---
  var table = document.getElementById('queue-table');
  if (table) {
    var currentSort = { key: null, asc: true };

    table.querySelectorAll('th[data-sort]').forEach(function (th) {
      th.addEventListener('click', function () {
        var key = th.dataset.sort;
        if (currentSort.key === key) {
          currentSort.asc = !currentSort.asc;
        } else {
          currentSort.key = key;
          currentSort.asc = true;
        }
        sortTable(key, currentSort.asc);
        updateSortIndicators(th, currentSort.asc);
      });
    });

    function getRowSortValue(row, key) {
      switch (key) {
        case 'equipment-name': return row.dataset.equipmentName.toLowerCase();
        case 'severity': return parseInt(row.dataset.severityPriority, 10);
        case 'area': return row.dataset.area.toLowerCase();
        case 'age': return parseInt(row.dataset.ageSeconds, 10);
        case 'status': return row.dataset.status.toLowerCase();
        case 'assignee': return row.dataset.assignee.toLowerCase();
        default: return '';
      }
    }

    function sortTable(key, asc) {
      var tbody = table.querySelector('tbody');
      var rows = Array.from(tbody.querySelectorAll('tr.queue-row'));
      rows.sort(function (a, b) {
        var va = getRowSortValue(a, key);
        var vb = getRowSortValue(b, key);
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
      });
      rows.forEach(function (row) { tbody.appendChild(row); });
    }

    function updateSortIndicators(activeTh, asc) {
      table.querySelectorAll('.sort-indicator').forEach(function (el) {
        el.textContent = '';
      });
      activeTh.querySelector('.sort-indicator').textContent = asc ? ' \u25B2' : ' \u25BC';
    }
  }

  // --- Queue filtering ---
  var areaFilter = document.getElementById('area-filter');
  var statusFilter = document.getElementById('status-filter');

  if (areaFilter && statusFilter) {
    function applyFilters() {
      var areaVal = areaFilter.value;
      var statusVal = statusFilter.value;
      var visibleCount = 0;

      // Filter table rows (canonical count source)
      document.querySelectorAll('.queue-row').forEach(function (row) {
        var areaMatch = !areaVal || row.dataset.areaId === areaVal;
        var statusMatch = !statusVal || row.dataset.status === statusVal;
        var visible = areaMatch && statusMatch;
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
      });

      // Filter mobile cards (mirrors table row visibility)
      document.querySelectorAll('.queue-card').forEach(function (card) {
        var areaMatch = !areaVal || card.dataset.areaId === areaVal;
        var statusMatch = !statusVal || card.dataset.status === statusVal;
        var link = card.closest('a');
        if (link) {
          link.style.display = (areaMatch && statusMatch) ? '' : 'none';
        }
      });

      // Show/hide empty state
      var emptyEl = document.getElementById('queue-empty');
      if (emptyEl) {
        emptyEl.classList.toggle('d-none', visibleCount > 0);
      }
    }

    areaFilter.addEventListener('change', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
  }
});
