<?php
/**
 * Seed an API client and a user API token on a disposable GLPI test instance.
 *
 * Run inside the GLPI container:
 *     SEED_APP_TOKEN=... SEED_USER_TOKEN=... php seed_api_client.php
 *
 * Why this exists instead of a plain SQL INSERT: since GLPI 11.0.3 the
 * `are_apiclients_tokens_encrypted` setting makes GLPI store app tokens
 * encrypted with the instance key, so a plaintext INSERT into glpi_apiclients
 * is rejected at authentication time with ERROR_WRONG_APP_TOKEN_PARAMETER.
 * Going through GLPI's own APIClient class applies whatever the running
 * version expects.
 *
 * Test-only. Never run this against a production instance: it rewrites the
 * 'glpi' user's API token.
 */

chdir('/var/www/glpi');

$configDir = getenv('GLPI_CONFIG_DIR') ?: '/var/glpi/config';

// Only the web entrypoint defines this; GLPIKey needs it to read the instance
// key used to encrypt app tokens, so under CLI we must define it ourselves.
// GLPI_ROOT, by contrast, is defined by GLPI's own constants.php - defining it
// here would abort the Composer autoloader.
if (!defined('GLPI_CONFIG_DIR')) {
    define('GLPI_CONFIG_DIR', $configDir);
}

require_once('vendor/autoload.php');
include_once('inc/includes.php');

$dbConfig = $configDir . '/config_db.php';
if (!file_exists($dbConfig)) {
    fwrite(STDERR, "database config not found at {$dbConfig}\n");
    exit(1);
}
require_once($dbConfig);

global $DB;
$DB = new DB();
if (!$DB->connected) {
    fwrite(STDERR, "could not connect to the GLPI database\n");
    exit(1);
}

$appToken  = getenv('SEED_APP_TOKEN');
$userToken = getenv('SEED_USER_TOKEN');
if (!$appToken || !$userToken) {
    fwrite(STDERR, "SEED_APP_TOKEN and SEED_USER_TOKEN must be set\n");
    exit(1);
}

// Idempotent: drop any client left by a previous run.
$DB->delete('glpi_apiclients', ['name' => 'glpi-rest integration tests']);

$client = new APIClient();
$id = $client->add([
    'entities_id'      => 0,
    'is_recursive'     => 1,
    'name'             => 'glpi-rest integration tests',
    'is_active'        => 1,
    'ipv4_range_start' => null,   // no IP restriction: requests arrive from the
    'ipv4_range_end'   => null,   // Docker bridge gateway, not 127.0.0.1
    'app_token'        => $appToken,
    'dolog_method'     => 0,
]);

if (!$id) {
    fwrite(STDERR, "APIClient::add() failed\n");
    exit(2);
}
echo "api client created (id={$id})\n";

// The token must go through User::update(): GLPI normalises it there, and a
// plain SQL write is rejected at authentication time.
//
// updateInDB() writes the row and only then calls Log::constructHistory(),
// which needs a web request context and fatals under CLI. The write has
// already landed at that point, so we swallow the error here; enable-api.sh
// then proves the token really works by calling initSession.
$user = new User();
if (!$user->getFromDBbyName('glpi')) {
    fwrite(STDERR, "user 'glpi' not found" . PHP_EOL);
    exit(3);
}
try {
    $user->update([
        'id'             => $user->getID(),
        'api_token'      => $userToken,
        'api_token_date' => date('Y-m-d H:i:s'),
    ]);
} catch (\Throwable $e) {
    fwrite(STDERR, "note: history logging failed after the write (expected under CLI)" . PHP_EOL);
}
echo "user api token set\n";
