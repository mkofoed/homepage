(() => {
    const root = document.querySelector("[data-request-lifecycle-url]");
    if (!root) {
        return;
    }

    const button = document.getElementById("request-lifecycle-button");
    const status = document.getElementById("request-lifecycle-status");
    const correlation = document.getElementById("request-lifecycle-correlation");
    const stages = new Map(
        [...root.querySelectorAll("[data-lifecycle-stage]")].map((element) => [element.dataset.lifecycleStage, element]),
    );

    const setStage = (stageName, state, detail) => {
        const stage = stages.get(stageName);
        if (!stage) {
            return;
        }

        stage.dataset.state = state;
        stage.querySelector("small").textContent = detail;
    };

    const resetStages = () => {
        stages.forEach((stage) => {
            stage.dataset.state = "waiting";
            stage.querySelector("small").textContent = "Waiting";
        });
    };

    const getCsrfToken = () => {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    };

    const websocketUrl = (correlationId) => {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        return `${protocol}//${window.location.host}/ws/request-lifecycle/${correlationId}/`;
    };

    const startTrace = () => {
        const correlationId = crypto.randomUUID();
        const socket = new WebSocket(websocketUrl(correlationId));
        let completed = false;

        button.disabled = true;
        resetStages();
        correlation.hidden = false;
        correlation.textContent = `trace:${correlationId}`;
        status.textContent = "Opening the real-time channel...";
        setStage("websocket", "running", "Connecting");

        const timeout = window.setTimeout(() => {
            if (socket.readyState !== WebSocket.OPEN) {
                socket.close();
                setStage("websocket", "error", "Unavailable");
                status.textContent = "The real-time channel could not be opened.";
                button.disabled = false;
            }
        }, 5000);

        socket.addEventListener("open", async () => {
            window.clearTimeout(timeout);
            setStage("websocket", "complete", "Connected");
            status.textContent = "Trace started. Following the request...";

            try {
                const response = await fetch(root.dataset.requestLifecycleUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                    body: JSON.stringify({ correlation_id: correlationId }),
                });
                const result = await response.json();
                if (!response.ok) {
                    const error = new Error(result.error || "The trace could not be started.");
                    error.status = response.status;
                    throw error;
                }
            } catch (error) {
                if (error.status === 429) {
                    setStage("django", "throttled", "Rate limited for 20 seconds");
                } else {
                    setStage("django", "error", "Not started");
                }
                status.textContent = error.message;
                button.disabled = false;
                socket.close();
            }
        });

        socket.addEventListener("message", (event) => {
            const update = JSON.parse(event.data);
            setStage(update.stage, update.status, update.detail);

            if (update.status === "error") {
                status.textContent = update.detail;
                button.disabled = false;
                socket.close();
                return;
            }

            if (update.stage === "celery" && update.status === "complete") {
                completed = true;
                status.textContent = "Complete: Django, Redis, Celery, and WebSocket all participated.";
                button.disabled = false;
                window.setTimeout(() => socket.close(), 500);
            }
        });

        socket.addEventListener("close", () => {
            window.clearTimeout(timeout);
            if (!completed && button.disabled) {
                button.disabled = false;
            }
        });

        socket.addEventListener("error", () => {
            setStage("websocket", "error", "Connection error");
        });
    };

    button.addEventListener("click", startTrace);
})();
