// ==================== CONFIGURATION ====================
const DB_FOLDER_NAME = "LOOM_DATA";
const DB_FILE_NAME = "LOOM_DB.json";
const BACKUP_FOLDER_NAME = "LOOM_BACKUPS";

// ==================== GESTION DES FICHIERS ====================

/**
 * Obtient le dossier de travail, le crée s'il n'existe pas
 */
function getWorkFolder() {
  var folders = DriveApp.getFoldersByName(DB_FOLDER_NAME);
  if (folders.hasNext()) return folders.next();
  return DriveApp.createFolder(DB_FOLDER_NAME);
}

/**
 * Obtient le dossier de sauvegarde
 */
function getBackupFolder() {
  var workFolder = getWorkFolder();
  var folders = workFolder.getFoldersByName(BACKUP_FOLDER_NAME);
  if (folders.hasNext()) return folders.next();
  return workFolder.createFolder(BACKUP_FOLDER_NAME);
}

/**
 * Obtient le fichier DB principal (crée s'il n'existe pas)
 */
function getDbFile() {
  var folder = getWorkFolder();
  var files = folder.getFilesByName(DB_FILE_NAME);
  if (files.hasNext()) return files.next();
  return folder.createFile(DB_FILE_NAME, JSON.stringify(getDefaultData()));
}

/**
 * Retourne la structure de données par défaut
 */
function getDefaultData() {
  return {
    "strands": [
      {
        "name": "⚪ CONVERGENCE",
        "color": "#ffffff",
        "events": []
      }
    ],
    "metadata": {
      "lastUpdate": new Date().toISOString(),
      "version": "1.0"
    }
  };
}

/**
 * Crée une sauvegarde datée du fichier DB
 */
function createBackup() {
  var dbFile = getDbFile();
  var backupFolder = getBackupFolder();
  var timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd_HH-mm-ss");
  var backupFile = backupFolder.createFile(
    DB_FILE_NAME.replace(".json", "_" + timestamp + ".json"),
    dbFile.getBlob().getDataAsString()
  );
  return backupFile;
}

/**
 * Récupère l'historique des sauvegardes (max 10)
 */
function listBackups() {
  var backupFolder = getBackupFolder();
  var files = backupFolder.getFiles();
  var backups = [];
  while (files.hasNext()) {
    var file = files.next();
    backups.push({
      "name": file.getName(),
      "date": file.getLastUpdated(),
      "size": file.getSize()
    });
  }
  return backups.sort((a, b) => b.date - a.date);
}

/**
 * Restaure une sauvegarde par nom de fichier
 */
function restoreBackup(backupName) {
  var backupFolder = getBackupFolder();
  var files = backupFolder.getFilesByName(backupName);
  if (!files.hasNext()) return { "status": "error", "message": "Backup not found" };
  
  var backupFile = files.next();
  var dbFile = getDbFile();
  dbFile.setContent(backupFile.getBlob().getDataAsString());
  
  return { "status": "ok", "message": "Restored from " + backupName };
}

// ==================== API WEB ====================

/**
 * GET - Récupère le JSON complet
 */
function doGet(e) {
  var dbFile = getDbFile();
  var content = dbFile.getBlob().getDataAsString();
  return ContentService.createTextOutput(content || "{}").setMimeType(ContentService.MimeType.JSON);
}

/**
 * POST - Met à jour le JSON avec verrous
 */
function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000);
    
    // Parse les données entrantes
    var newData = JSON.parse(e.postData.contents);
    
    // Validation basique
    if (!newData.strands || !Array.isArray(newData.strands)) {
      throw new Error("Invalid data format: missing 'strands' array");
    }
    
    // Crée une sauvegarde avant d'écrire
    createBackup();
    
    // Ajoute les métadonnées
    newData.metadata = newData.metadata || {};
    newData.metadata.lastUpdate = new Date().toISOString();
    newData.metadata.version = "1.0";
    
    // Écrit les données
    getDbFile().setContent(JSON.stringify(newData, null, 2));
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "ok",
      "items": newData.strands.reduce((sum, s) => sum + s.events.length, 0),
      "timestamp": newData.metadata.lastUpdate
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

// ==================== UTILITAIRES ====================

/**
 * Retourne les informations du fichier DB
 */
function getDbInfo() {
  var dbFile = getDbFile();
  var content = JSON.parse(dbFile.getBlob().getDataAsString());
  return {
    "fileName": dbFile.getName(),
    "fileId": dbFile.getId(),
    "lastModified": dbFile.getLastUpdated(),
    "size": dbFile.getSize(),
    "strands": content.strands.length,
    "events": content.strands.reduce((sum, s) => sum + s.events.length, 0),
    "metadata": content.metadata
  };
}

/**
 * Nettoie les anciennes sauvegardes (garde les 10 dernières)
 */
function cleanOldBackups(keep = 10) {
  var backupFolder = getBackupFolder();
  var files = backupFolder.getFiles();
  var filesList = [];
  while (files.hasNext()) {
    filesList.push(files.next());
  }
  filesList.sort((a, b) => b.getLastUpdated() - a.getLastUpdated());
  
  var deleted = 0;
  for (var i = keep; i < filesList.length; i++) {
    filesList[i].setTrashed(true);
    deleted++;
  }
  return { "status": "ok", "deleted": deleted };
}