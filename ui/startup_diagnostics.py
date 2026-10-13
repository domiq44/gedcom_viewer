import time


def measure_startup_callback(widget, callback_name, callback):
    def measured_callback(event):
        root = widget.winfo_toplevel()
        if not getattr(root, "_startup_diagnostics_enabled", False):
            return callback(event)

        started_at = time.perf_counter()
        try:
            return callback(event)
        finally:
            elapsed = time.perf_counter() - started_at
            metrics = root._startup_callback_metrics.setdefault(
                callback_name, [0, 0.0, 0.0]
            )
            metrics[0] += 1
            metrics[1] += elapsed
            metrics[2] = max(metrics[2], elapsed)

    return measured_callback
