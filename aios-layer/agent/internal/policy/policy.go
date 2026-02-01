package policy

import "errors"

type Policy struct {
	MaxGPUsPerUser int
	MaxDurationSec int
}

func (p Policy) ValidateRequest(existingLeases int, requestedDuration int) error {
	if p.MaxGPUsPerUser > 0 && existingLeases >= p.MaxGPUsPerUser {
		return errors.New("gpu quota exceeded")
	}
	if p.MaxDurationSec > 0 && requestedDuration > p.MaxDurationSec {
		return errors.New("requested duration exceeds policy")
	}
	if requestedDuration <= 0 {
		return errors.New("invalid duration")
	}
	return nil
}
