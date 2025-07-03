const Joi = require('joi');

// Validation schemas
const schemas = {
  signup: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(6).required(),
    first_name: Joi.string().min(1).max(50).required(),
    last_name: Joi.string().min(1).max(50).required(),
    phone: Joi.string().optional(),
    preferred_city: Joi.string().valid('vancouver', 'toronto', 'calgary').optional()
  }),

  login: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
  }),

  swipe: Joi.object({
    job_id: Joi.string().required(),
    swipe_action: Joi.string().valid('apply', 'pass', 'save').required(),
    session_id: Joi.string().when('$isAnonymous', {
      is: true,
      then: Joi.required(),
      otherwise: Joi.optional()
    })
  })
};

// Validation middleware factory
const createValidationMiddleware = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, { 
      abortEarly: false,
      stripUnknown: true 
    });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      return res.status(400).json({
        success: false,
        message: 'Validation error',
        errors: errors
      });
    }

    req.body = value;
    next();
  };
};

// City validation middleware
const validateCity = (req, res, next) => {
  const validCities = ['vancouver', 'toronto', 'calgary'];
  const city = req.query.city?.toLowerCase();

  if (city && !validCities.includes(city)) {
    return res.status(400).json({
      success: false,
      message: 'Invalid city',
      valid_cities: validCities
    });
  }

  next();
};

// Swipe validation with context
const validateSwipe = (req, res, next) => {
  const isAnonymous = req.route.path.includes('anonymous');
  const schema = schemas.swipe;
  
  const { error, value } = schema.validate(req.body, { 
    context: { isAnonymous },
    abortEarly: false,
    stripUnknown: true 
  });

  if (error) {
    const errors = error.details.map(detail => ({
      field: detail.path.join('.'),
      message: detail.message
    }));

    return res.status(400).json({
      success: false,
      message: 'Validation error',
      errors: errors
    });
  }

  req.body = value;
  next();
};

module.exports = {
  validateSignup: createValidationMiddleware(schemas.signup),
  validateLogin: createValidationMiddleware(schemas.login),
  validateSwipe,
  validateCity
};