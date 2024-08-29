document.addEventListener('DOMContentLoaded', function() {
    const observer = new MutationObserver(function(mutationsList) {
        for (const mutation of mutationsList) {
            if (mutation.type === 'childList') {
                const rightPanel = document.getElementById('right-panel');
                if (rightPanel) {
                    // console.log('Right panel found:', rightPanel);
                    // rightPanel.classList.remove('collapsed'); // Ensure the panel is not collapsed initially
                    rightPanel.style.width = ''; // Remove inline width style
                    //rightPanel.style.transition = 'width 1s ease'; // Add ease transition

                    // console.log('Right panel found:', rightPanel);
                    observer.disconnect(); // Stop observing after finding the element
                }
            }
        }
    });

    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
});
