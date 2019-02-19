from typing import List

from boto3 import client


def list_s3_contents(bucket_name: str, prefix: str) -> List[str]:
    s3_conn = client('s3')  # type: BaseClient  ## again assumes boto.cfg setup, assume AWS S3
    s3_result = s3_conn.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    print(s3_result)
    if 'Contents' not in s3_result:
        print(s3_result)
        return []

    file_list = []
    for key in s3_result['Contents']:
        file_list.append(key['Key'])
    print(f"List count = {len(file_list)}")

    # when we got more than 1000 items aws will truncate the result
    while s3_result['IsTruncated']:
        continuation_key = s3_result['NextContinuationToken']
        s3_result = s3_conn.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/",
                                            ContinuationToken=continuation_key)
        for key in s3_result['Contents']:
            file_list.append(key['Key'])
        print(f"List count = {len(file_list)}")
    return file_list
