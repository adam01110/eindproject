import "basecoat-css/basecoat";
import "basecoat-css/select";
import "basecoat-css/tabs";

const MOBILE_SIDEBAR_MEDIA_QUERY = "(max-width: 767px)";

function setInitialSidebarState() {
    const sidebar = document.getElementById("app-sidebar");
    if (!sidebar || !window.matchMedia(MOBILE_SIDEBAR_MEDIA_QUERY).matches) {
        return;
    }

    sidebar.setAttribute("aria-hidden", "true");
    sidebar.setAttribute("inert", "");

    for (const button of document.querySelectorAll<HTMLElement>("[data-sidebar-open]")) {
        button.setAttribute("aria-expanded", "false");
    }

    for (const button of document.querySelectorAll<HTMLElement>(
        "[data-sidebar-collapse], [data-sidebar-pin]",
    )) {
        button.setAttribute("aria-expanded", "false");
    }
}

setInitialSidebarState();
