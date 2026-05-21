// Farmer Automation - Tauri Main Entry
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let _ = app
                .get_webview_window("main")
                .expect("no main window")
                .set_focus();
        }))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Backend Go sẽ được chạy thủ công trong terminal riêng
            // Chạy: cd backend-go && go run main.go
            println!("Backend mode: Manual. Please start Go backend separately.");

            // Window Close Event -> Exit App
            let main_window = app.get_webview_window("main").unwrap();
            let app_handle = app.handle().clone();
            main_window.on_window_event(move |event| {
                if let tauri::WindowEvent::Destroyed = event {
                     println!("App window closing...");
                     app_handle.exit(0);
                }
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
