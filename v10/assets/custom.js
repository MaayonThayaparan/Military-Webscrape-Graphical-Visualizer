document.addEventListener('DOMContentLoaded', function() {
    function updateHeadersWithLinks() {
        const columnLinksStore = document.getElementById('column-links-store').textContent;
        let columnLinks = {};
        if (columnLinksStore) {
            columnLinks = JSON.parse(columnLinksStore);
        }
        
        const headers = document.querySelectorAll('.dash-spreadsheet th.dash-header');
        if (headers.length === 0) {
            console.log("Headers not found, retrying...");
            setTimeout(updateHeadersWithLinks, 100);  // Retry after 100ms
            return;
        }

        headers.forEach(header => {
            const content = header.textContent.trim();
            if (columnLinks[content] && !header.innerHTML.includes('href')) {  // Check if not already converted to link
                console.log(`Updating header: ${content}`);
                header.innerHTML = `<a href="${columnLinks[content]}" target="_blank">${content}</a>`;
            }
        });
    }

    updateHeadersWithLinks();  // Initial call

    // Set up a MutationObserver to handle dynamic changes such as sorting or filtering
    const observer = new MutationObserver(updateHeadersWithLinks);
    observer.observe(document.body, { childList: true, subtree: true });
});
