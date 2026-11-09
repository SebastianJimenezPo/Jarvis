use rustpotter::{Rustpotter, RustpotterConfig, SampleFormat, WakewordRef,
                WakewordRefBuildFromFiles, WakewordSave};
use serde_json::json;
use std::io::{self, Read, Write};

fn emit(value: serde_json::Value) -> Result<(), String> {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    writeln!(out, "{value}").map_err(|e| e.to_string())?;
    out.flush().map_err(|e| e.to_string())
}

fn run(args: &[String]) -> Result<(), String> {
    if args.get(1).map(String::as_str) == Some("calibrate") {
        if !(8..=11).contains(&args.len()) {
            return Err("calibrate OUTPUT SAMPLE1.wav ... SAMPLE5..8.wav".into());
        }
        let reference = WakewordRef::new_from_sample_files(
            "Jarvis".into(), None, None, args[3..].to_vec(), 13)?;
        reference.save_to_file(&args[2])?;
        return emit(json!({"type":"calibrated", "protocol":1}));
    }
    if args.len() != 5 || args[1] != "detect" {
        return Err("detect REFERENCE THRESHOLD AVG_THRESHOLD".into());
    }
    let mut config = RustpotterConfig::default();
    config.fmt.sample_rate = 16000;
    config.fmt.channels = 1;
    config.fmt.sample_format = SampleFormat::I16;
    config.detector.threshold = args[3].parse().map_err(|_| "invalid threshold")?;
    config.detector.avg_threshold = args[4].parse().map_err(|_| "invalid avg threshold")?;
    let mut detector = Rustpotter::new(&config)?;
    detector.add_wakeword_from_file("jarvis", &args[2])?;
    let frame = detector.get_bytes_per_frame();
    emit(json!({"type":"ready", "protocol":1, "engine":"rustpotter-3.0.2",
                "frame_bytes":frame, "sample_rate":16000, "encoding":"s16le"}))?;
    let mut input = io::stdin().lock();
    let mut audio = vec![0u8; frame];
    loop {
        let mut header = [0u8; 4];
        // EOF is graceful only between messages; a truncated header is an error.
        match input.read(&mut header[..1]) {
            Ok(0) => break,
            Ok(_) => (),
            Err(e) => return Err(e.to_string()),
        }
        input.read_exact(&mut header[1..]).map_err(|e| e.to_string())?;
        let length = u32::from_le_bytes(header) as usize;
        if length == 0 { break; }
        if length != frame { return Err(format!("expected {frame} bytes, got {length}")); }
        input.read_exact(&mut audio).map_err(|e| e.to_string())?;
        let result = detector.process_bytes(&audio);
        let event = match result {
            Some(hit) => json!({"type":"result", "detected":true, "score":hit.score}),
            None => json!({"type":"result", "detected":false}),
        };
        emit(event)?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = run(&std::env::args().collect::<Vec<_>>()) {
        eprintln!("{error}");
        let _ = emit(json!({"type":"error", "message":error}));
        std::process::exit(1);
    }
}
