-- Prevent hard-deleting POIs that have dependent content or narration history.
-- Existing orphan narration_events.poi_id rows must be resolved before applying.
BEGIN;

ALTER TABLE poi_translations
  DROP CONSTRAINT poi_translations_poi_id_fkey,
  ADD CONSTRAINT poi_translations_poi_id_fkey
    FOREIGN KEY (poi_id) REFERENCES pois(id) ON DELETE RESTRICT;

ALTER TABLE poi_images
  DROP CONSTRAINT poi_images_poi_id_fkey,
  ADD CONSTRAINT poi_images_poi_id_fkey
    FOREIGN KEY (poi_id) REFERENCES pois(id) ON DELETE RESTRICT;

ALTER TABLE poi_audios
  DROP CONSTRAINT poi_audios_poi_id_fkey,
  ADD CONSTRAINT poi_audios_poi_id_fkey
    FOREIGN KEY (poi_id) REFERENCES pois(id) ON DELETE RESTRICT;

ALTER TABLE qr_codes
  DROP CONSTRAINT qr_codes_poi_id_fkey,
  ADD CONSTRAINT qr_codes_poi_id_fkey
    FOREIGN KEY (poi_id) REFERENCES pois(id) ON DELETE RESTRICT;

ALTER TABLE narration_events
  ADD CONSTRAINT narration_events_poi_id_fkey
    FOREIGN KEY (poi_id) REFERENCES pois(id) ON DELETE RESTRICT;

COMMIT;
