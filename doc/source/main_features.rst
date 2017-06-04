Glare Features
==============


Glare main features:

-   Catalog of custom artifacts
    You can create your own artifact and use it.
    This must be a class which is subtype of BaseArtifact class.
    artifact type represents user entity, and define specific properties.
    Example: #TBD#

-   Artifact Versioning - each artifact can be supplemented with the version in SemVer format (http://semver.org/).
    E.G. 1.0 --> 1.0.0, 1-alpha --> 1.1.0#Am i right?#

-   Support of multiple binary objects per artifact.
    For example: User can create new artifact type as Amazon image and specify
    three blobs (binary objects) there: kernal, Ram disk and memory and later access them directly.

-   Structured properties - artifact may contain structured attributes like 'Dict' and 'List'.
    Blob dictionary: Artifact may have a folder. Inside the folder user may put his blobs (files).
    'Dict and 'List' of primitive types: for metadata, artifact can have properties such as
    dictionary of string, dictionary of floats,  list of integers, list of strings ETC.

-   Validators - are objects that can be attached to a filed to perform additional
    checks. For example, if validator MinLen(1) is attached to a string field it
    checks that the string value is non empty. Validator ForbiddenChars("/", ",")
    validates that there shouldn't be slashes and commas in the string

-   Advanced filtering with various operators.
    Each artifact field has filter_ops - a list of available filter operators for the field.
    There are seven available operators: 'eq', 'neq', 'lt', 'lte', 'gt', 'gte', 'in'
    Example: to get all the artifacts with version different than 2.0, we will use neq operator.

-   Advanced Sorting - artifacts REST API accepts multiple sort keys and directions,
    in order to retrieve data in any sort order and direction.
    For example data can be retrieved by ascending order of names, and descending order
    of versions.

-   Artifact visibility - defines who may have an access to Artifact. Initially there are 2 options:
    1.  private artifact is accessible by its owner and admin only.
        When artifact is 'drafted' its visibility is always private.
    2.  public, when all users have an access to the artifact by default.
        It's allowed to change visibility only when artifact has active status.


-   Links between artifacts- one artifact may depend on another.
    Artifact Link is field type that defines soft dependency of the Artifact from another Artifact.
    It is an url that allows user to obtain some Artifact data
    ?how can we use it?

-   Automatic schema generation for each artifact type.
    Each artifact type has its own unique properties. Glare has special api
    to reveal artifact's properties. (would it reveal all the properties?)

-   Microversion support and Backend support, provided by glance_store
    ?What does it mean? how can we use it?

-   Artifact life cycle
    draft -> active -> deactivated -> active -> delete
    [picture]
    #How can i upload a picture?#