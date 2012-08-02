define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
    ],
function($, Backbone, _, _s, Util){
    // unique id generator.
    var _uniqueId = 0;
    var getUniqueId = function(){
        _uniqueId++;
        return 'GeoRefineId_' + _uniqueId;
    };

    var keyFunc = function(namespace, id){
        return _s.sprintf('_{{%s:%s}}_', namespace, id);
    }

    // Returns the class name of the argument or undefined if
    // class is not known.
    var getObjectClass = function(obj) {
        // Define list of classes.
        var knownClasses = {
            'Backbone.Model': Backbone.Model,
            'Backbone.Collection': Backbone.Collection,
        };
        // If we find object's class, return it.
        for (var className in knownClasses){
            if (obj instanceof knownClasses[className]){
                return className;
            }
        }
        return undefined;
    };

    // Initialize serializers object.
    var serializers = {};
    
    // Backbone.Model serializer.
    serializers['Backbone.Model'] = function(model, registry){

        // Get key for model.
        var modelKey = keyFunc('Backbone.Model', model.cid);

        // If model is not in the registry...
        if (! registry[modelKey]){
            // Initialize serialized model object.
            var serializedModel = {};

            // For each model attribute + cid...
            _.each(_.extend(model.toJSON(), {cid: model.cid}), function(value, attr){
                // Serialize the value.
                serializedModel[attr] = serialize(value, registry);
            });

            // Save the serialized model to the registry.
            registry[modelKey] = serializedModel;
        }

        // Return the model key.
        return modelKey;
    };

    // Backbone.Collection serializer.
    serializers['Backbone.Collection'] = function(collection, registry, opts){

        // Assign random cid to collection if not yet assigned.
        collection.cid = collection.cid || getUniqueId();

        // Get key for collection.
        var collectionKey = keyFunc('Backbone.Collection', collection.cid);

        // If collection is not in the registry...
        if (! registry[collectionKey]){
            // Initialize serializedCollection
            var serializedCollection = {};

            // Add serialized models.
            serializedCollection.models = [];
            _.each(collection.models, function(model){
                serializedCollection.models.push(serialize(model, registry));
            });

            // Save the serialized collection the registry.
            registry[collectionKey] = serializedCollection;
        }

        // Return the collection key.
        return collectionKey;

    };

    // Given an object, serialize it.
    // This process will also register it (and its sub-objects)
    // in the registry.
    var serialize = function(obj, registry){

        // Get the type of the object.
        var clazz = getObjectClass(obj);

        // If the type has a serializer, serialize the value.
        if (serializer = serializers[clazz]){
            return serializer(obj, registry);
        }
        // Otherwise return it as-is.
        else{
            return obj;
        }
    };


    // Initialize deserializers.
    var deserializers = {};

    // Backbone.Model deserializer.
    deserializers['Backbone.Model'] = function(modelKey, deserializedRegistry, serializedRegistry){

        // If key is not in the registry...
        if (! deserializedRegistry[modelKey]){
            // Initialize attributes hash for deserialized model.
            var attrs = {};

            // Get the serialized model from the registry.
            var serializedModel = serializedRegistry[modelKey];

            // For each attr in the serializedModel...
            _.each(serializedModel, function(value, attr){
                // Save the deserialized value to the attrs.
                attrs[attr] = deserialize(value, deserializedRegistry, serializedRegistry);
            });

            // Create a model from the attributes.
            deserializedModel = new Backbone.Model(attrs);

            // Save the deserialized model to the registry.
            deserializedRegistry[modelKey] = deserializedModel;
        }

        // Return the deserialized model.
        return deserializedRegistry[modelKey];
    };

    // Backbone.Collection deserializer.
    deserializers['Backbone.Collection'] = function(collectionKey, deserializedRegistry, serializedRegistry){

        // If collection is not in the registry...
        if (! deserializedRegistry[collectionKey]){

            // Get the serialized collection from the registry.
            var serializedCollection = serializedRegistry[collectionKey];

            // Get deserialized models.
            var deserializedModels = [];
            _.each(serializedCollection.models, function(model){
                deserializedModels.push(deserialize(model, deserializedRegistry, serializedRegistry));
            });

            // Create collection from the models.
            var deserializedCollection = new Backbone.Collection(deserializedModels);

            // Save the deserialized collection the registry.
            deserializedRegistry[collectionKey] = deserializedCollection;
        }

        // Return the deserialized collection.
        return deserializedRegistry[collectionKey];

    };

    // Regular expression for parsing registry keys.
    var keyRe = /_{{(.*):(.*)}}_/;
    
    // Given a serialized object and a registry, deserialize it.
    var deserialize = function(obj, deserializedRegistry, serializedRegistry){
        // If object is a string and matches the token pattern, deserialize it with the corresponding
        // deserializer.
        if (typeof obj == 'string'){
            if (match = keyRe.exec(obj)){
                clazz = match[1];
                // Use deserializer for class if it exists.
                if (deserializer = deserializers[clazz]){
                    return deserializer(obj, deserializedRegistry, serializedRegistry);
                }
            }
        }
        // Otherwise if the object is an array or object, iterate through its items.
        else if (typeof obj == 'object'){
            var deserializedObj = null;
            if (obj instanceof Array){
                deserializedObj = [];
                _.each(obj, function(value){
                    deserializedObj.push(deserialize(value, deserializedRegistry, serializedRegistry));
                });
            }
            else{
                deserializedObj = {};
                _.each(obj, function(value, attr){
                    deserializedObj[attr] = deserialize(value, deserializedRegistry, serializedRegistry);
                });
            }
            return deserializedObj;
        }

        // Otherwise return it as-is.
        return obj;
    };


    // Objects to expose.
    var serializationUtil = {
        serialize: serialize,
        deserialize: deserialize
    };

    return serializationUtil;
});
