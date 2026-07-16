# Logical Input Schema

Data kind: **spectrum**

Required logical fields:

- `source_id`
- `wavelength`
- `flux_or_counts`
- `uncertainty_or_inverse_variance`
- `mask_or_quality`
- `instrument_configuration`
- `reference_redshift_or_class_if_used`

Map archive-specific names to these logical fields in a versioned configuration file. Fail clearly when a required field is absent.
