/**
 * Private webhook for the TeachCL Streamlit app.
 * Paste this file into a Google Apps Script project owned by the researcher.
 */

function doPost(event) {
  try {
    var request = JSON.parse(event.postData.contents || "{}");
    var properties = PropertiesService.getScriptProperties();
    var expectedToken = properties.getProperty("ARCHIVE_TOKEN") || "";
    var rootFolderId = properties.getProperty("ROOT_FOLDER_ID") || "";

    if (!expectedToken || !rootFolderId || !constantTimeEquals_(request.token, expectedToken)) {
      return jsonResponse_({ ok: false, error: "unauthorized" });
    }

    if (request.action === "allocate_participant_id") {
      return jsonResponse_({ ok: true, participant_id: allocateParticipantId_(properties) });
    }

    if (!["content", "analysis", "feedback", "sheet"].includes(request.kind)) {
      return jsonResponse_({ ok: false, error: "invalid_record_type" });
    }
    if (!/^[a-f0-9]{32}$/.test(request.session_id || "") || !request.record) {
      return jsonResponse_({ ok: false, error: "invalid_record" });
    }

    if (request.kind === "sheet") {
      if (!request.record || !/^[a-f0-9]{32}$/.test(request.session_id || "") ||
          String(request.record.session_id || "") !== request.session_id) {
        return jsonResponse_({ ok: false, error: "invalid_sheet_record" });
      }
      var spreadsheetId = properties.getProperty("SPREADSHEET_ID") || "";
      var sheetName = properties.getProperty("SHEET_NAME") || "Experiment Data";
      if (!spreadsheetId) return jsonResponse_({ ok: false, error: "spreadsheet_not_configured" });
      var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(sheetName);
      if (!sheet) sheet = SpreadsheetApp.openById(spreadsheetId).insertSheet(sheetName);
      return jsonResponse_({ ok: true, rows: upsertSheetSession_(sheet, request.record) });
    }

    var rootFolder = DriveApp.getFolderById(rootFolderId);
    var targetFolder = getOrCreateFolder_(rootFolder, request.kind);
    var participantId = String(request.record.participant_id || "00");
    var stem = request.kind + "_" + participantId + "_" + request.session_id;
    var savedNames;

    if (request.kind === "feedback") {
      if (typeof request.record.feedback_text !== "string" ||
          typeof request.record.chart_base64 !== "string") {
        return jsonResponse_({ ok: false, error: "invalid_feedback_record" });
      }
      var feedbackName = stem + ".txt";
      var chartName = stem + ".png";
      upsertTextFile_(targetFolder, feedbackName, request.record.feedback_text);
      upsertBlobFile_(targetFolder, chartName, request.record.chart_base64, "image/png");
      savedNames = [feedbackName, chartName];
    } else {
      var content = request.kind === "content"
        ? formatConversation_(request.record)
        : JSON.stringify(request.record, null, 2);
      if (content.length > 9 * 1024 * 1024) {
        return jsonResponse_({ ok: false, error: "record_too_large" });
      }
      var fileName = stem + ".txt";
      upsertTextFile_(targetFolder, fileName, content);
      savedNames = [fileName];
    }

    return jsonResponse_({ ok: true, names: savedNames });
  } catch (error) {
    console.error("Research archive failed: " + error.message);
    return jsonResponse_({ ok: false, error: "archive_failed" });
  }
}

function upsertSheetSession_(sheet, record) {
  var headers = ["ID", "role", "messages", "timestamp", "coding", "pattern", "visualized feedback", "session_id"];
  if (sheet.getLastRow() === 0) sheet.appendRow(headers);
  else {
    var existingHeaders = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), headers.length)).getValues()[0];
    headers.forEach(function(header, index) {
      if (existingHeaders[index] !== header) throw new Error("sheet_headers_mismatch");
    });
  }

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      var sessionValues = sheet.getRange(2, headers.length, lastRow - 1, 1).getValues();
      for (var i = sessionValues.length - 1; i >= 0; i--) {
        if (String(sessionValues[i][0]) === String(record.session_id)) sheet.deleteRow(i + 2);
      }
    }

    var codingByTurn = {};
    var coding = record.coding || {};
    ((coding.turns) || []).forEach(function(item) {
      codingByTurn[String(item.turn)] = (item.codes || []).join(", ");
    });
    var pattern = record.pattern ? JSON.stringify(record.pattern) : "";
    var visualizedFeedback = [record.feedback || "", record.visualization ? "Visualization: " + JSON.stringify(record.visualization) : ""]
      .filter(String).join("\n\n");
    var rows = (record.messages || []).map(function(message) {
      var codingText = message.role === "user" ? (codingByTurn[String(message.turn_number)] || "") : "";
      return [
        record.participant_id, message.role, message.content, message.timestamp,
        codingText, pattern, visualizedFeedback, record.session_id
      ].map(safeSheetCell_);
    });
    if (rows.length) sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, headers.length).setValues(rows);
    return rows.length;
  } finally {
    lock.releaseLock();
  }
}

function safeSheetCell_(value) {
  var text = String(value == null ? "" : value);
  return /^[=+\-@]/.test(text) ? "'" + text : text;
}

function allocateParticipantId_(properties) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var lastNumber = parseInt(properties.getProperty("LAST_PARTICIPANT_NUMBER") || "0", 10);
    if (!isFinite(lastNumber) || lastNumber < 0) lastNumber = 0;
    var nextNumber = lastNumber + 1;
    properties.setProperty("LAST_PARTICIPANT_NUMBER", String(nextNumber));
    return nextNumber < 10 ? "0" + nextNumber : String(nextNumber);
  } finally {
    lock.releaseLock();
  }
}

function formatConversation_(record) {
  var lines = [
    "Participant: " + (record.participant_id || ""),
    "Session: " + (record.session_id || ""),
    "Created: " + (record.created_at || ""),
    "Status: " + (record.status || ""),
    ""
  ];
  (record.messages || []).forEach(function(message) {
    lines.push("[" + (message.timestamp || "") + "] " + String(message.role || "").toUpperCase());
    lines.push(message.content || "");
    lines.push("");
  });
  return lines.join("\n");
}

function upsertTextFile_(folder, name, content) {
  var files = folder.getFilesByName(name);
  if (files.hasNext()) {
    files.next().setContent(content);
  } else {
    folder.createFile(name, content, "text/plain");
  }
}

function upsertBlobFile_(folder, name, base64Content, mimeType) {
  var files = folder.getFilesByName(name);
  while (files.hasNext()) files.next().setTrashed(true);
  var bytes = Utilities.base64Decode(base64Content);
  folder.createFile(Utilities.newBlob(bytes, mimeType, name));
}

function getOrCreateFolder_(parent, name) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var folders = parent.getFoldersByName(name);
    return folders.hasNext() ? folders.next() : parent.createFolder(name);
  } finally {
    lock.releaseLock();
  }
}

function constantTimeEquals_(provided, expected) {
  if (typeof provided !== "string" || provided.length !== expected.length) return false;
  var difference = 0;
  for (var i = 0; i < expected.length; i++) {
    difference |= provided.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return difference === 0;
}

function jsonResponse_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
