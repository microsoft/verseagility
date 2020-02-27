import { OutputSchema } from "../output";

// Parsers are used to convert data from any format to the NLP toolkit format

export interface IParser {
    parse(fileBuffer: Buffer): Promise<Array<OutputSchema>>;
}