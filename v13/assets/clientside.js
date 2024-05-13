if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    open_hyperlink: function(hyperlinks) {
        // Assume hyperlinks are passed as an array of {column: url} mappings
        document.querySelectorAll('.dash-header').forEach((header, index) => {
            if (hyperlinks[header.textContent.trim()]) {
                header.onclick = () => {
                    window.open(hyperlinks[header.textContent.trim()], '_blank');
                };
            }
        });
        return null;
    }
};