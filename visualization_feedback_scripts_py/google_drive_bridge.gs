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
    if (!["conversation", "analysis"].includes(request.kind)) {
      return jsonResponse_({ ok: false, error: "invalid_record_type" });
    }
    if (!/^[a-f0-9]{32}$/.test(request.session_id || "") || !request.record) {
      return jsonResponse_({ ok: false, error: "invalid_record" });
    }

    var content = JSON.stringify(request.record, null, 2);
    if (content.length > 9 * 1024 * 1024) {
      return jsonResponse_({ ok: false, error: "record_too_large" });
    }

    var folderName = request.kind === "conversation" ? "conversations" : "analyses";
    var fileName = request.kind + "_" + request.session_id + ".json";
    var rootFolder = DriveApp.getFolderById(rootFolderId);
    var targetFolder = getOrCreateFolder_(rootFolder, folderName);
    var files = targetFolder.getFilesByName(fileName);
    var savedFile;
    if (files.hasNext()) {
      savedFile = files.next();
      savedFile.setContent(content);
    } else {
      savedFile = targetFolder.createFile(fileName, content, "application/json");
    }

    return jsonResponse_({ ok: true, name: fileName, file_id: savedFile.getId() });
  } catch (error) {
    console.error("Research archive failed: " + error.message);
    return jsonResponse_({ ok: false, error: "archive_failed" });
  }
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
